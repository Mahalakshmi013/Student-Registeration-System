

-- PL/SQL Package: reg_pkg
-- All procedures and functions included in this package. 
-- This package implements Procedures 2–7 from the project specification

SET DEFINE OFF;

-- PACKAGE HEADER

CREATE OR REPLACE PACKAGE reg_pkg IS
    -- Procedure 2: Display procedures (for all 8 tables)
    PROCEDURE show_students;
    PROCEDURE show_courses;
    PROCEDURE show_classes;
    PROCEDURE show_course_credit;
    PROCEDURE show_score_grade;
    PROCEDURE show_g_enrollments;
    PROCEDURE show_prerequisites;
    PROCEDURE show_logs;

    -- Procedure 3 & 4: Query procedures
    PROCEDURE list_students_in_class(p_classid IN classes.classid%TYPE);
    PROCEDURE list_prerequisites(p_dept IN courses.dept_code%TYPE, p_course IN courses.course#%TYPE);

    -- Procedure 5–7: Core logic procedures
    PROCEDURE enroll_grad_student(p_b# IN students.b#%TYPE, p_classid IN classes.classid%TYPE);
    PROCEDURE drop_grad_student(p_b# IN students.b#%TYPE, p_classid IN classes.classid%TYPE);
    PROCEDURE delete_student(p_b# IN students.b#%TYPE);
END reg_pkg;
/



-- PACKAGE BODY

CREATE OR REPLACE PACKAGE BODY reg_pkg IS

    -- Procedure 2: Display all table contents (8 procedures)
    PROCEDURE show_students IS
    BEGIN
        FOR rec IN (SELECT * FROM students) LOOP
            DBMS_OUTPUT.PUT_LINE(rec.b# || ' ' || rec.first_name || ' ' || rec.last_name);
        END LOOP;
    END;

    PROCEDURE show_courses IS
    BEGIN
        FOR rec IN (SELECT * FROM courses) LOOP
            DBMS_OUTPUT.PUT_LINE(rec.dept_code || rec.course# || ': ' || rec.title);
        END LOOP;
    END;

    PROCEDURE show_classes IS
    BEGIN
        FOR rec IN (SELECT * FROM classes) LOOP
            DBMS_OUTPUT.PUT_LINE(rec.classid || ' ' || rec.course# || ' ' || rec.semester || ' ' || rec.year);
        END LOOP;
    END;

    PROCEDURE show_course_credit IS
    BEGIN
        FOR rec IN (SELECT * FROM course_credit) LOOP
            DBMS_OUTPUT.PUT_LINE('Course ' || rec.course# || ' - ' || rec.credits || ' credits');
        END LOOP;
    END;

    PROCEDURE show_score_grade IS
    BEGIN
        FOR rec IN (SELECT * FROM score_grade) LOOP
            DBMS_OUTPUT.PUT_LINE(rec.score || ': ' || rec.lgrade);
        END LOOP;
    END;

    PROCEDURE show_g_enrollments IS
    BEGIN
        FOR rec IN (SELECT * FROM g_enrollments) LOOP
            DBMS_OUTPUT.PUT_LINE(rec.g_b# || ' - ' || rec.classid || ' - ' || NVL(TO_CHAR(rec.score), 'N/A'));
        END LOOP;
    END;

    PROCEDURE show_prerequisites IS
    BEGIN
        FOR rec IN (SELECT * FROM prerequisites) LOOP
            DBMS_OUTPUT.PUT_LINE(rec.dept_code || rec.course# || ' ← ' || rec.pre_dept_code || rec.pre_course#);
        END LOOP;
    END;

    PROCEDURE show_logs IS
    BEGIN
        FOR rec IN (SELECT * FROM logs ORDER BY log# DESC) LOOP
            DBMS_OUTPUT.PUT_LINE('[' || rec.log# || '] ' || rec.user_name || ' ' || rec.operation ||
                                 ' on ' || rec.table_name || ' → ' || rec.tuple_keyvalue);
        END LOOP;
    END;

    -- Procedure 3: List students in a given class
    -- Input: classid; output: b#, first name, last name
    -- Error if classid not found
    PROCEDURE list_students_in_class(p_classid IN classes.classid%TYPE) IS
        v_exists NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_exists FROM classes WHERE classid = p_classid;
        IF v_exists = 0 THEN
            DBMS_OUTPUT.PUT_LINE('The classid is invalid.');
            RETURN;
        END IF;

        FOR rec IN (
            SELECT s.b#, s.first_name, s.last_name
            FROM students s JOIN g_enrollments g ON s.b# = g.g_b#
            WHERE g.classid = p_classid
        ) LOOP
            DBMS_OUTPUT.PUT_LINE(rec.b# || ' ' || rec.first_name || ' ' || rec.last_name);
        END LOOP;
    END;

   
    -- Procedure 4: List direct and indirect prerequisites
    -- Recursive SQL using CONNECT BY
    PROCEDURE list_prerequisites(p_dept IN courses.dept_code%TYPE, p_course IN courses.course#%TYPE) IS
        v_exists NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_exists FROM courses WHERE dept_code = p_dept AND course# = p_course;
        IF v_exists = 0 THEN
            DBMS_OUTPUT.PUT_LINE('dept_code || course# does not exist.');
            RETURN;
        END IF;

        FOR rec IN (
            SELECT pre_dept_code || pre_course# AS prerequisite
            FROM prerequisites
            START WITH dept_code = p_dept AND course# = p_course
            CONNECT BY PRIOR pre_dept_code = dept_code AND PRIOR pre_course# = course#
        ) LOOP
            DBMS_OUTPUT.PUT_LINE(rec.prerequisite);
        END LOOP;
    END;

   
    -- Procedure 5: Enroll graduate student into a class
    -- Validations: student, level, class existence, semester, limit, duplicate, 5-class max, prerequisite
    PROCEDURE enroll_grad_student(p_b# IN students.b#%TYPE, p_classid IN classes.classid%TYPE) IS
        v_level students.st_level%TYPE;
        v_year classes.year%TYPE;
        v_semester classes.semester%TYPE;
        v_count NUMBER;
        v_limit NUMBER;
        v_size NUMBER;
        v_exists NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_exists FROM students WHERE b# = p_b#;
        IF v_exists = 0 THEN DBMS_OUTPUT.PUT_LINE('The B# is invalid.'); RETURN; END IF;

        SELECT st_level INTO v_level FROM students WHERE b# = p_b#;
        IF v_level NOT IN ('master', 'PhD') THEN DBMS_OUTPUT.PUT_LINE('This is not a graduate student.'); RETURN; END IF;

        SELECT COUNT(*) INTO v_exists FROM classes WHERE classid = p_classid;
        IF v_exists = 0 THEN DBMS_OUTPUT.PUT_LINE('The classid is invalid.'); RETURN; END IF;

        SELECT year, semester INTO v_year, v_semester FROM classes WHERE classid = p_classid;
        IF v_year != 2021 OR v_semester != 'Spring' THEN DBMS_OUTPUT.PUT_LINE('Cannot enroll into a class from a previous semester.'); RETURN; END IF;

        SELECT limit, class_size INTO v_limit, v_size FROM classes WHERE classid = p_classid;
        IF v_size >= v_limit THEN DBMS_OUTPUT.PUT_LINE('The class is already full.'); RETURN; END IF;

        SELECT COUNT(*) INTO v_exists FROM g_enrollments WHERE g_b# = p_b# AND classid = p_classid;
        IF v_exists > 0 THEN DBMS_OUTPUT.PUT_LINE('The student is already in the class.'); RETURN; END IF;

        SELECT COUNT(*) INTO v_count
        FROM g_enrollments g JOIN classes c ON g.classid = c.classid
        WHERE g.g_b# = p_b# AND c.semester = 'Spring' AND c.year = 2021;
        IF v_count >= 5 THEN DBMS_OUTPUT.PUT_LINE('Students cannot be enrolled in more than five classes in the same semester.'); RETURN; END IF;

        FOR pre IN (
            SELECT pre_dept_code, pre_course#
            FROM prerequisites
            WHERE dept_code || course# = (
                SELECT dept_code || course# FROM classes WHERE classid = p_classid
            )
        ) LOOP
            SELECT COUNT(*) INTO v_exists
            FROM g_enrollments g
            JOIN classes c ON g.classid = c.classid
            JOIN score_grade sg ON g.score = sg.score
            WHERE g.g_b# = p_b#
              AND c.dept_code = pre.pre_dept_code
              AND c.course# = pre.pre_course#
              AND sg.lgrade <= 'C';
            IF v_exists = 0 THEN DBMS_OUTPUT.PUT_LINE('Prerequisite not satisfied.'); RETURN; END IF;
        END LOOP;

        INSERT INTO g_enrollments(g_b#, classid, score) VALUES (p_b#, p_classid, NULL);
        DBMS_OUTPUT.PUT_LINE('Enrollment successful.');
    END;


    -- Procedure 6: Drop a graduate student from a class
    -- Validations: enrollment, semester, only-class check
    PROCEDURE drop_grad_student(p_b# IN students.b#%TYPE, p_classid IN classes.classid%TYPE) IS
        v_level students.st_level%TYPE;
        v_exists NUMBER;
        v_count NUMBER;
        v_year classes.year%TYPE;
        v_semester classes.semester%TYPE;
    BEGIN
        SELECT COUNT(*) INTO v_exists FROM students WHERE b# = p_b#;
        IF v_exists = 0 THEN DBMS_OUTPUT.PUT_LINE('The B# is invalid.'); RETURN; END IF;

        SELECT st_level INTO v_level FROM students WHERE b# = p_b#;
        IF v_level NOT IN ('master', 'PhD') THEN DBMS_OUTPUT.PUT_LINE('This is not a graduate student.'); RETURN; END IF;

        SELECT COUNT(*) INTO v_exists FROM classes WHERE classid = p_classid;
        IF v_exists = 0 THEN DBMS_OUTPUT.PUT_LINE('The classid is invalid.'); RETURN; END IF;

        SELECT COUNT(*) INTO v_exists FROM g_enrollments WHERE g_b# = p_b# AND classid = p_classid;
        IF v_exists = 0 THEN DBMS_OUTPUT.PUT_LINE('The student is not enrolled in the class.'); RETURN; END IF;

        SELECT year, semester INTO v_year, v_semester FROM classes WHERE classid = p_classid;
        IF v_year != 2021 OR v_semester != 'Spring' THEN DBMS_OUTPUT.PUT_LINE('Only enrollment in the current semester can be dropped.'); RETURN; END IF;

        SELECT COUNT(*) INTO v_count
        FROM g_enrollments g JOIN classes c ON g.classid = c.classid
        WHERE g.g_b# = p_b# AND c.year = 2021 AND c.semester = 'Spring';
        IF v_count = 1 THEN DBMS_OUTPUT.PUT_LINE('This is the only class for this student in Spring 2021 and cannot be dropped.'); RETURN; END IF;

        DELETE FROM g_enrollments WHERE g_b# = p_b# AND classid = p_classid;
        DBMS_OUTPUT.PUT_LINE('Drop successful.');
    END;

    -- Procedure 7: Delete a student from the system
    -- Triggers will delete associated enrollments and log the deletion
    PROCEDURE delete_student(p_b# IN students.b#%TYPE) IS
        v_exists NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_exists FROM students WHERE b# = p_b#;
        IF v_exists = 0 THEN
            DBMS_OUTPUT.PUT_LINE('The B# is invalid.');
            RETURN;
        END IF;

        DELETE FROM students WHERE b# = p_b#;
        DBMS_OUTPUT.PUT_LINE('Student deleted successfully.');
    END;

END reg_pkg;
/

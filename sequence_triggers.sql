
-- 1. Sequence for logs
CREATE SEQUENCE log_seq
START WITH 1000
INCREMENT BY 1;


-- 2. Trigger: Log INSERT/DELETE on G_Enrollments
CREATE OR REPLACE TRIGGER trg_log_enrollment
AFTER INSERT OR DELETE ON g_enrollments
FOR EACH ROW
DECLARE
    log_action VARCHAR2(6);
BEGIN
    IF INSERTING THEN
        log_action := 'insert';
    ELSIF DELETING THEN
        log_action := 'delete';
    END IF;

    INSERT INTO logs(log#, user_name, op_time, table_name, operation, tuple_keyvalue)
    VALUES (
        log_seq.NEXTVAL,
        USER,
        SYSDATE,
        'G_ENROLLMENTS',
        log_action,
        :OLD.g_B# || ',' || :OLD.classid
    );
END;
/

-- 3. Trigger: Log DELETE on Students
CREATE OR REPLACE TRIGGER trg_log_delete_student
AFTER DELETE ON students
FOR EACH ROW
BEGIN
    INSERT INTO logs(log#, user_name, op_time, table_name, operation, tuple_keyvalue)
    VALUES (
        log_seq.NEXTVAL,
        USER,
        SYSDATE,
        'STUDENTS',
        'delete',
        :OLD.B#
    );
END;
/

-- 4. Trigger: Auto-update class size
CREATE OR REPLACE TRIGGER trg_update_class_size
AFTER INSERT OR DELETE ON g_enrollments
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        UPDATE classes
        SET class_size = class_size + 1
        WHERE classid = :NEW.classid;
    ELSIF DELETING THEN
        UPDATE classes
        SET class_size = class_size - 1
        WHERE classid = :OLD.classid;
    END IF;
END;
/



-- 5. Trigger: Cascade delete g_enrollments when a student is removed (manual trigger version)
CREATE OR REPLACE TRIGGER trg_cascade_delete_enrollments
AFTER DELETE ON students
FOR EACH ROW
BEGIN
    DELETE FROM g_enrollments
    WHERE g_B# = :OLD.B#;
END;
/

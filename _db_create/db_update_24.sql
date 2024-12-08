ALTER TABLE `teacher` 
ADD COLUMN `teacher_department_secretary` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Секретарь кафедры' AFTER `teacher_department_leader`;
SET SQL_SAFE_UPDATES = 0;

UPDATE `teacher` set `teacher_department_secretary` = 1 where `teacher_rank` = 'секретарь' and `department_id` BETWEEN 1601 AND 1606;

COMMIT;



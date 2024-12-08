ALTER TABLE `teacher` 
ADD COLUMN `teacher_dean_staff` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Сотрудник деканата',
ADD COLUMN `teacher_department_leader` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Зав. кафедрой';

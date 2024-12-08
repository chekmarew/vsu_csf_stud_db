ALTER TABLE `teacher` 
ADD COLUMN `teacher_academic_degree` VARCHAR(128) NULL COMMENT 'Учёная степень' AFTER `teacher_rank`;

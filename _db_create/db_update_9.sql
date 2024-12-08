ALTER TABLE `subject` 
ADD COLUMN `subject_code` VARCHAR(16) NOT NULL DEFAULT 0 COMMENT 'Код предмета по учебному плану' AFTER `subject_id`,
DROP INDEX `subject_name_UNIQUE` ;

ALTER TABLE `subject` 
ADD UNIQUE INDEX `subject_UNIQUE` (`subject_code`, `subject_name`);


ALTER TABLE `curriculum_unit` 
DROP INDEX `UNIQUE` ,
ADD UNIQUE INDEX `UNIQUE` (`stud_group_id`, `subject_id`, `mark_type`);
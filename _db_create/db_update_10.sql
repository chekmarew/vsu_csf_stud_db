ALTER TABLE `curriculum_unit` 
ADD COLUMN `curriculum_unit_code` VARCHAR(16) NOT NULL DEFAULT '0' COMMENT 'Шифр по учебному плану' AFTER `curriculum_unit_id`;

ALTER TABLE `subject`
DROP INDEX `subject_UNIQUE` , 
DROP COLUMN `subject_code`,
ADD UNIQUE INDEX `subject_UNIQUE` (`subject_name`);
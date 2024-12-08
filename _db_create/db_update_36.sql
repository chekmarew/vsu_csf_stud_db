ALTER TABLE `curriculum_unit` 
ADD COLUMN `moodle_id` INT UNSIGNED NULL COMMENT 'Ссылка на учебный курс в moodle' AFTER `hours_att_3`;

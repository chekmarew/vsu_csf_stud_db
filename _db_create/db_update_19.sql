ALTER TABLE `curriculum_unit_status_hist` 
ADD COLUMN `pass_department` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Ведомость сдана на кафедру';
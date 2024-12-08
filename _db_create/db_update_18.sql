ALTER TABLE `curriculum_unit` 
ADD COLUMN `pass_department` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Ведомость сдана на кафедру' AFTER `allow_edit_practice_teacher_att_mark_append_ball`;
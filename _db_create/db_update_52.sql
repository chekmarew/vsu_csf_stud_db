ALTER TABLE `curriculum_unit`
ADD COLUMN `use_topic` ENUM('none', 'coursework', 'project_seminar') CHARACTER SET 'latin1' COLLATE 'latin1_general_ci' NOT NULL DEFAULT 'none' COMMENT 'Единица учебного плана относится к работе с руководителем' AFTER `mark_type`;

ALTER TABLE `att_mark`
ADD COLUMN `teacher_id` INT(11) UNSIGNED,
ADD COLUMN `work_theme` VARCHAR(1000);

ALTER TABLE `att_mark`
ADD CONSTRAINT `fk_att_mark_teacher`
  FOREIGN KEY (`teacher_id`)
  REFERENCES `teacher` (`teacher_id`)
  ON DELETE NO ACTION
  ON UPDATE CASCADE;


ALTER TABLE `att_mark_hist`
ADD COLUMN `teacher_id` INT(11) UNSIGNED,
ADD COLUMN `work_theme` VARCHAR(1000);

ALTER TABLE `att_mark_hist`
ADD CONSTRAINT `fk_att_mark_hist_teacher`
  FOREIGN KEY (`teacher_id`)
  REFERENCES `teacher` (`teacher_id`)
  ON DELETE NO ACTION
  ON UPDATE CASCADE;

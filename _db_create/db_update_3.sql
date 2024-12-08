ALTER TABLE `curriculum_unit` ADD COLUMN `curriculum_unit_status` ENUM('att_1', 'att_2', 'att_3', 'exam', 'close') NOT NULL DEFAULT 'att_1';

ALTER TABLE `student` 
ADD COLUMN `card_number` BIGINT(20) UNSIGNED NULL COMMENT 'Номер карты (пропуск)',
ADD COLUMN `stud_group_leader` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Староста группы',
ADD UNIQUE INDEX `card_number_UNIQUE` (`card_number` ASC);

CREATE TABLE `att_mark_hist` (
  `att_mark_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на att_mark(att_mark_id)',
  `stime` DATETIME NOT NULL COMMENT 'Время начала действия записи',
  `etime` DATETIME NULL COMMENT 'Время окончания действия записи (если null, то действует на текущий момент)',
  `admin_user_id` INT UNSIGNED NULL,
  `teacher_id` INT UNSIGNED NULL,
  `att_mark_1` TINYINT(3) UNSIGNED NULL,
  `att_mark_2` TINYINT(3) UNSIGNED NULL,
  `att_mark_3` TINYINT(3) UNSIGNED NULL,
  `att_mark_exam` TINYINT(3) UNSIGNED NULL,
  `att_mark_append_ball` TINYINT(3) UNSIGNED NULL,
  PRIMARY KEY (`att_mark_id`, `stime`))
COMMENT = 'История изменения таблицы att_mark';

ALTER TABLE `att_mark_hist` 
ADD INDEX `fk_att_mark_hist_admin_user_id_idx` (`admin_user_id` ASC),
ADD INDEX `fk_att_mark_hist_teacher_id_idx` (`teacher_id` ASC);
ALTER TABLE `att_mark_hist` 
ADD CONSTRAINT `fk_att_mark_hist_att_mark_id`
  FOREIGN KEY (`att_mark_id`)
  REFERENCES `att_mark` (`att_mark_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE,
ADD CONSTRAINT `fk_att_mark_hist_admin_user_id`
  FOREIGN KEY (`admin_user_id`)
  REFERENCES `admin_user` (`admin_user_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION,
ADD CONSTRAINT `fk_att_mark_hist_teacher_id`
  FOREIGN KEY (`teacher_id`)
  REFERENCES `teacher` (`teacher_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;

CREATE TABLE `curriculum_unit_status_hist` (
  `curriculum_unit_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на curriculum_unit(curriculum_unit_id)',
  `stime` DATETIME NOT NULL COMMENT 'Время начала действия записи',
  `etime` DATETIME NULL COMMENT 'Время окончания действия записи (если null, то действует на текущий момент)',
  `admin_user_id` INT UNSIGNED NOT NULL,
  `curriculum_unit_status` ENUM('att_1', 'att_2', 'att_3', 'exam', 'close') NOT NULL,
  PRIMARY KEY (`curriculum_unit_id`, `stime`))
COMMENT = 'История изменения поля curriculum_unit_status в таблице curriculum_unit';

ALTER TABLE `curriculum_unit_status_hist` 
ADD INDEX `fk_curriculum_unit_status_hist_admin_user_id_idx` (`admin_user_id` ASC) VISIBLE;

ALTER TABLE `curriculum_unit_status_hist` 
ADD CONSTRAINT `fk_curriculum_unit_status_hist_id`
  FOREIGN KEY (`curriculum_unit_id`)
  REFERENCES `curriculum_unit` (`curriculum_unit_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE,
ADD CONSTRAINT `fk_curriculum_unit_status_hist_admin_user_id`
  FOREIGN KEY (`admin_user_id`)
  REFERENCES `admin_user` (`admin_user_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;


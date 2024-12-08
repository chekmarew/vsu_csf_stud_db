ALTER TABLE `teacher` 
ADD COLUMN `teacher_allow_start_with_att3` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Флаг - разрешать преподавателю править сразу 3 аттестации' AFTER `teacher_contacts`;



ALTER TABLE `curriculum_unit` 
ADD COLUMN `practice_teacher_id` INT(11) UNSIGNED NULL COMMENT 'Преподаватель практических(лабораторных занятий) - ID преподавателя  из таблицы teacher',
ADD COLUMN `allow_edit_practice_teacher_att_mark_1` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать результаты 1 аттестации',
ADD COLUMN `allow_edit_practice_teacher_att_mark_2` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать результаты 2 аттестации',
ADD COLUMN `allow_edit_practice_teacher_att_mark_3` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать результаты 3 аттестации',
ADD COLUMN `allow_edit_practice_teacher_att_mark_exam` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать оценку за экзамен',
ADD COLUMN `allow_edit_practice_teacher_att_mark_append_ball` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать доп. балл',
ADD INDEX `fk_curriculum_unit_practice_teacher_idx` (`practice_teacher_id` ASC);

ALTER TABLE `curriculum_unit` 
ADD CONSTRAINT `fk_curriculum_unit_practice_teacher`
  FOREIGN KEY (`practice_teacher_id`)
  REFERENCES `teacher` (`teacher_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;
  
  

ALTER TABLE `curriculum_unit_status_hist` 
ADD COLUMN `teacher_id` INT(11) UNSIGNED NULL AFTER `admin_user_id`,
CHANGE COLUMN `admin_user_id` `admin_user_id` INT(11) UNSIGNED NULL ,
ADD INDEX `fk_curriculum_unit_status_teacher_id_idx` (`teacher_id` ASC);


ALTER TABLE `curriculum_unit_status_hist` 
ADD CONSTRAINT `fk_curriculum_unit_status_teacher_id`
  FOREIGN KEY (`teacher_id`)
  REFERENCES `teacher` (`teacher_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;
  
  
  
ALTER TABLE `curriculum_unit_status_hist` 
ADD COLUMN `practice_teacher_id` INT(11) UNSIGNED NULL COMMENT 'Преподаватель практических(лабораторных занятий) - ID преподавателя  из таблицы teacher',
ADD COLUMN `allow_edit_practice_teacher_att_mark_1` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать результаты 1 аттестации',
ADD COLUMN `allow_edit_practice_teacher_att_mark_2` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать результаты 2 аттестации',
ADD COLUMN `allow_edit_practice_teacher_att_mark_3` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать результаты 3 аттестации',
ADD COLUMN `allow_edit_practice_teacher_att_mark_exam` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать оценку за экзамен',
ADD COLUMN `allow_edit_practice_teacher_att_mark_append_ball` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать доп. балл',
ADD INDEX `fk_curriculum_unit_status_hist_practice_teacher_idx` (`practice_teacher_id` ASC);



ALTER TABLE `curriculum_unit_status_hist` 
ADD CONSTRAINT `fk_curriculum_unit_status_hist_practice_teacher`
  FOREIGN KEY (`practice_teacher_id`)
  REFERENCES `teacher` (`teacher_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;
  
  
ALTER TABLE `curriculum_unit_status_hist` 
ADD COLUMN `hours_att_1` TINYINT(3) UNSIGNED NOT NULL DEFAULT 0,
ADD COLUMN `hours_att_2` TINYINT(3) UNSIGNED NOT NULL DEFAULT 0,
ADD COLUMN `hours_att_3` TINYINT(3) UNSIGNED NOT NULL DEFAULT 0;

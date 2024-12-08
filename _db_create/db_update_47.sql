ALTER TABLE `stud_group` ADD COLUMN `weeks_training` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Недель теоретического обучения (в расписании занятий не отображать =0)' AFTER `session_end_date`;
ALTER TABLE `curriculum_unit` 
ADD COLUMN `hours_lect` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Часов лекционных занятий' AFTER `hours_att_3`,
ADD COLUMN `hours_pract` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Часов практических занятий' AFTER `hours_lect`,
ADD COLUMN `hours_lab` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Часов лабораторных занятий' AFTER `hours_pract`

;


CREATE TABLE `scheduled_lesson` (
  `scheduled_lesson_id` BIGINT UNSIGNED NOT NULL,
  `curriculum_unit_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на curriculum_unit(curriculum_unit_id)',
  `stud_group_subnums` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Подгруппы побитовая маска (0-если группа не делится на подгруппы, 1-только 1-я, 2-только 2-я, 3-две подгруппы )',
  `teacher_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на teacher(teacher_id)',
  `week_day` TINYINT UNSIGNED NOT NULL COMMENT 'День недели',
  `week_type` TINYINT UNSIGNED NOT NULL COMMENT '1-числитель;2-знаменатель;3-каждую неделю',
  `lesson_num` TINYINT UNSIGNED NOT NULL COMMENT 'Номер пары',
  `classroom` VARCHAR(6) NULL,
  `scheduled_lesson_comment` VARCHAR(4000) NULL COMMENT 'Комметарий к занятию (обязателен если classroom is null)',
  PRIMARY KEY (`scheduled_lesson_id`),
  INDEX `fk_scheduled_lesson_teacher_id_idx` (`teacher_id` ASC) VISIBLE,
  INDEX `fk_scheduled_lesson_curriculum_unit_id_idx` (`curriculum_unit_id` ASC) VISIBLE,
  INDEX `fk_scheduled_lesson_num_idx` (`lesson_num` ASC) VISIBLE,
  INDEX `fk_scheduled_lesson_classroom` (`classroom` ASC) VISIBLE,
  CONSTRAINT `fk_scheduled_lesson_teacher_id`
    FOREIGN KEY (`teacher_id`)
    REFERENCES `teacher` (`teacher_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_scheduled_lesson_curriculum_unit_id`
    FOREIGN KEY (`curriculum_unit_id`)
    REFERENCES `curriculum_unit` (`curriculum_unit_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_scheduled_lesson_num`
    FOREIGN KEY (`lesson_num`)
    REFERENCES `lesson_time` (`lesson_num`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_scheduled_lesson_classroom`
    FOREIGN KEY (`classroom`)
    REFERENCES `classroom` (`classroom`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
COMMENT = 'Занятие по расписанию' DEFAULT CHARSET=utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;





CREATE TABLE `scheduled_lesson_draft` (
  `scheduled_lesson_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `curriculum_unit_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на curriculum_unit(curriculum_unit_id)',
  `stud_group_subnums` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Подгруппы побитовая маска (0-если группа не делится на подгруппы, 1-только 1-я, 2-только 2-я, 3-две подгруппы )',
  `teacher_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на teacher(teacher_id)',
  `week_day` TINYINT UNSIGNED NOT NULL COMMENT 'День недели',
  `week_type` TINYINT UNSIGNED NOT NULL COMMENT '1-числитель;2-знаменатель;3-каждую неделю',
  `lesson_num` TINYINT UNSIGNED NOT NULL COMMENT 'Номер пары',
  `classroom` VARCHAR(6) NULL,
  `scheduled_lesson_comment` VARCHAR(4000) NULL COMMENT 'Комметарий к занятию (обязателен если classroom is null)',
  PRIMARY KEY (`scheduled_lesson_id`),
  INDEX `fk_scheduled_lesson_draft_teacher_id_idx` (`teacher_id` ASC) VISIBLE,
  INDEX `fk_scheduled_lesson_draft_curriculum_unit_id_idx` (`curriculum_unit_id` ASC) VISIBLE,
  INDEX `fk_scheduled_lesson_draft_num_idx` (`lesson_num` ASC) VISIBLE,
  INDEX `fk_scheduled_lesson_draft_classroom` (`classroom` ASC) VISIBLE,
  CONSTRAINT `fk_scheduled_lesson_draft_teacher_id`
    FOREIGN KEY (`teacher_id`)
    REFERENCES `teacher` (`teacher_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_scheduled_lesson_draft_curriculum_unit_id`
    FOREIGN KEY (`curriculum_unit_id`)
    REFERENCES `curriculum_unit` (`curriculum_unit_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_scheduled_lesson_draft_num`
    FOREIGN KEY (`lesson_num`)
    REFERENCES `lesson_time` (`lesson_num`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_scheduled_lesson_draft_classroom`
    FOREIGN KEY (`classroom`)
    REFERENCES `classroom` (`classroom`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
COMMENT = 'Занятие по расписанию (черновик)' DEFAULT CHARSET=utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;




CREATE TABLE `subject_particular` (
  `subject_particular_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `subject_particular_name` VARCHAR(256) NOT NULL,
  `replaced_subject_id` INT UNSIGNED NOT NULL COMMENT 'Замена subject(subject_id)',
  PRIMARY KEY (`subject_particular_id`),
  UNIQUE INDEX `subject_particular_name_UNIQUE` (`subject_particular_name` ASC) VISIBLE,
  UNIQUE INDEX `replaced_subject_id_UNIQUE` (`replaced_subject_id` ASC) VISIBLE,
  CONSTRAINT `fk_subject_particular_replaced_subject_id`
    FOREIGN KEY (`replaced_subject_id`)
    REFERENCES `subject` (`subject_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
COMMENT = 'Особый предмет';


INSERT INTO `subject_particular` (`subject_particular_name`, `replaced_subject_id`) VALUES ('Русский язык для иностранцев', '2');
INSERT INTO `subject_particular` (`subject_particular_name`, `replaced_subject_id`) VALUES ('Профессиональное общение на русском языке (для иностранцев)', '273');
INSERT INTO `subject_particular` (`subject_particular_name`, `replaced_subject_id`) VALUES ('Военная подготовка', '247');

commit;


CREATE TABLE `student_subject_particular` (
  `student_id` BIGINT UNSIGNED NOT NULL,
  `subject_particular_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`student_id`, `subject_particular_id`),
  INDEX `fk_student_subject_particular_subject_particular_id_idx` (`subject_particular_id` ASC) VISIBLE,
  CONSTRAINT `fk_student_subject_particular_student_id`
    FOREIGN KEY (`student_id`)
    REFERENCES `student` (`student_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_student_subject_particular_subject_particular_id`
    FOREIGN KEY (`subject_particular_id`)
    REFERENCES `subject_particular` (`subject_particular_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
COMMENT = 'студенты, изучающие особые предметы subject_particular';


insert into student_subject_particular
select student_id, 1 from student where student_foreigner=1;
commit;


CREATE TABLE `scheduled_subject_particular` (
  `scheduled_subject_particular_id` BIGINT UNSIGNED NOT NULL,
  `stud_group_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на stud_group(stud_group_id)',
  `subject_particular_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на subject_particular(subject_particular_id)',
  `stud_group_subnums` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Подгруппы побитовая маска (0-если группа не делится на подгруппы, 1-только 1-я, 2-только 2-я, 3-две подгруппы )',
  `week_day` TINYINT UNSIGNED NOT NULL COMMENT 'День недели',
  `week_type` TINYINT UNSIGNED NOT NULL COMMENT '1-числитель;2-знаменатель;3-каждую неделю',
  `lesson_num` TINYINT UNSIGNED NOT NULL COMMENT 'Номер пары',
  `classroom` VARCHAR(6) NULL,
  `scheduled_subject_particular_comment` VARCHAR(4000) NULL COMMENT 'Комметарий к занятию',
  PRIMARY KEY (`scheduled_subject_particular_id`),
  INDEX `fk_scheduled_subject_particular_stud_group_idx` (`stud_group_id` ASC) VISIBLE,
  INDEX `fk_scheduled_lesson_num_idx` (`lesson_num` ASC) VISIBLE,
  INDEX `fk_scheduled_lesson_classroom` (`classroom` ASC) VISIBLE,
  CONSTRAINT `fk_scheduled_subject_particular_lesson_num`
    FOREIGN KEY (`lesson_num`)
    REFERENCES `lesson_time` (`lesson_num`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_scheduled_subject_particular_classroom`
    FOREIGN KEY (`classroom`)
    REFERENCES `classroom` (`classroom`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
COMMENT = 'Занятие по расписанию для особых предметов' DEFAULT CHARSET=utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;


ALTER TABLE `scheduled_subject_particular` 
ADD INDEX `fk_scheduled_subject_particular_idx` (`subject_particular_id` ASC) VISIBLE;


ALTER TABLE `scheduled_subject_particular` 
ADD CONSTRAINT `fk_scheduled_subject_particular_id`
  FOREIGN KEY (`subject_particular_id`)
  REFERENCES `subject_particular` (`subject_particular_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION,
ADD CONSTRAINT `fk_scheduled_subject_particular_stud_group_id`
  FOREIGN KEY (`stud_group_id`)
  REFERENCES `stud_group` (`stud_group_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;

CREATE TABLE `scheduled_subject_particular_draft` (
  `scheduled_subject_particular_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `stud_group_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на stud_group(stud_group_id)',
  `subject_particular_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на subject_particular(subject_particular_id)',
  `stud_group_subnums` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Подгруппы побитовая маска (0-если группа не делится на подгруппы, 1-только 1-я, 2-только 2-я, 3-две подгруппы )',
  `week_day` TINYINT UNSIGNED NOT NULL COMMENT 'День недели',
  `week_type` TINYINT UNSIGNED NOT NULL COMMENT '1-числитель;2-знаменатель;3-каждую неделю',
  `lesson_num` TINYINT UNSIGNED NOT NULL COMMENT 'Номер пары',
  `classroom` VARCHAR(6) NULL,
  `scheduled_subject_particular_comment` VARCHAR(4000) NULL COMMENT 'Комметарий к занятию',
  PRIMARY KEY (`scheduled_subject_particular_id`),
  INDEX `fk_scheduled_subject_particular_draft_stud_group_idx` (`stud_group_id` ASC) VISIBLE,
  INDEX `fk_scheduled_subject_particular_draft_lesson_draft_num_idx` (`lesson_num` ASC) VISIBLE,
  INDEX `fk_scheduled_subject_particular_draft_lesson_classroom` (`classroom` ASC) VISIBLE,
  CONSTRAINT `fk_scheduled_subject_particular_draft_lesson_num`
    FOREIGN KEY (`lesson_num`)
    REFERENCES `lesson_time` (`lesson_num`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_scheduled_subject_particular_draft_classroom`
    FOREIGN KEY (`classroom`)
    REFERENCES `classroom` (`classroom`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
COMMENT = 'Занятие по расписанию для особых предметов (черновик)' DEFAULT CHARSET=utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;


ALTER TABLE `scheduled_subject_particular_draft` 
ADD INDEX `fk_scheduled_subject_particular_draft_idx` (`subject_particular_id` ASC) VISIBLE;


ALTER TABLE `scheduled_subject_particular_draft` 
ADD CONSTRAINT `fk_scheduled_subject_particular_draft_id`
  FOREIGN KEY (`subject_particular_id`)
  REFERENCES `subject_particular` (`subject_particular_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION,
ADD CONSTRAINT `fk_scheduled_subject_particular_draft_stud_group_id`
  FOREIGN KEY (`stud_group_id`)
  REFERENCES `stud_group` (`stud_group_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;

ALTER TABLE `scheduled_lesson` 
ADD COLUMN `lesson_type` ENUM('lecture', 'pract', 'lab') CHARACTER SET 'latin1' COLLATE 'latin1_general_ci' NOT NULL COMMENT 'Тип занятия: лекции, практики, лабораторные' AFTER `stud_group_subnums`;

ALTER TABLE `scheduled_lesson_draft` 
ADD COLUMN `lesson_type` ENUM('lecture', 'pract', 'lab') CHARACTER SET 'latin1' COLLATE 'latin1_general_ci' NOT NULL COMMENT 'Тип занятия: лекции, практики, лабораторные' AFTER `stud_group_subnums`;


ALTER TABLE `scheduled_lesson` 
ADD COLUMN `lesson_form` ENUM('in_class', 'remote') CHARACTER SET 'latin1' COLLATE 'latin1_general_ci' NOT NULL DEFAULT 'in_class' COMMENT 'Форма занятия: очная, дистанционная' AFTER `lesson_type`;

ALTER TABLE `scheduled_lesson_draft` 
ADD COLUMN `lesson_form` ENUM('in_class', 'remote') CHARACTER SET 'latin1' COLLATE 'latin1_general_ci' NOT NULL DEFAULT 'in_class' COMMENT 'Форма занятия: очная, дистанционная' AFTER `lesson_type`;


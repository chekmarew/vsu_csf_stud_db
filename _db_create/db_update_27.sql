ALTER TABLE `curriculum_unit` 
ADD COLUMN `curriculum_unit_group_id` INT UNSIGNED NULL COMMENT 'Группа единиц учебных планов для одного преподавателя с разным названием предметов' AFTER `curriculum_unit_code`;

ALTER TABLE `curriculum_unit`
ADD UNIQUE INDEX `UNIQUE_curriculum_unit_group_id` (`stud_group_id` ASC, `curriculum_unit_group_id` ASC) VISIBLE;


CREATE TABLE `lesson` (
  `lesson_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `teacher_id` INT UNSIGNED NOT NULL,
  `lesson_date` DATE NOT NULL,
  `lesson_type` ENUM('seminar', 'lecture') NOT NULL DEFAULT 'seminar',
  `lesson_form` ENUM('in_class', 'remote') NOT NULL DEFAULT 'in_class',
  `lesson_comment` varchar(4000) NULL,
  PRIMARY KEY (`lesson_id`));

ALTER TABLE `lesson` 
ADD INDEX `fk_lesson_teacher_idx` (`teacher_id` ASC) VISIBLE;

ALTER TABLE `lesson` 
ADD CONSTRAINT `fk_lesson_teacher`
  FOREIGN KEY (`teacher_id`)
  REFERENCES `teacher` (`teacher_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;
  
 CREATE TABLE `lesson_curriculum_unit` (
  `lesson_id` BIGINT UNSIGNED NOT NULL,
  `curriculum_unit_id` INT UNSIGNED NOT NULL,
  `stud_group_subnums` TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`lesson_id`, `curriculum_unit_id`));
  
  
ALTER TABLE `lesson_curriculum_unit` 
ADD CONSTRAINT `fk_lesson`
  FOREIGN KEY (`lesson_id`)
  REFERENCES `lesson` (`lesson_id`)
  ON DELETE CASCADE
  ON UPDATE NO ACTION,
ADD CONSTRAINT `fk_curriculum_unit`
  FOREIGN KEY (`curriculum_unit_id`)
  REFERENCES `curriculum_unit` (`curriculum_unit_id`)
  ON DELETE CASCADE
  ON UPDATE NO ACTION;
  
  
 CREATE TABLE `lesson_student` (
  `lesson_id` BIGINT UNSIGNED NOT NULL,
  `curriculum_unit_id` INT UNSIGNED NOT NULL,
  `student_id` BIGINT UNSIGNED NOT NULL,
  `attendance` TINYINT(1) UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Отметка о присутствии: 0 - отсутствовал; 1 - присутствовал; 2 - отсутствовал по уважительной причине',
  `lesson_student_comment` varchar(4000) NULL,
  PRIMARY KEY (`lesson_id`, `curriculum_unit_id`, `student_id`),
  CHECK (attendance in (0, 1, 2)));

ALTER TABLE `lesson_student`
ADD UNIQUE INDEX `UNIQUE_lesson_student` (`lesson_id` ASC, `student_id` ASC) VISIBLE;

ALTER TABLE `lesson_student`
ADD CONSTRAINT `fk_lesson_student`
  FOREIGN KEY (`student_id`)
  REFERENCES `student` (`student_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE,
ADD CONSTRAINT `fk_lesson_curriculum_unit`
  FOREIGN KEY (`lesson_id` , `curriculum_unit_id`)
  REFERENCES `lesson_curriculum_unit` (`lesson_id` , `curriculum_unit_id`)
  ON DELETE CASCADE
  ON UPDATE NO ACTION;
  
  
  
 CREATE TABLE `lesson_time` (
  `lesson_num` TINYINT(1) UNSIGNED NOT NULL COMMENT 'Номер пары',
  `lesson_stime` TIME NOT NULL COMMENT 'Время начала пары',
  `lesson_etime` TIME NOT NULL COMMENT 'Время окончания пары',
  PRIMARY KEY (`lesson_num`))
COMMENT = 'Часы звонков';


INSERT INTO `lesson_time` (`lesson_num`, `lesson_stime`, `lesson_etime`) VALUES ('1', '8:00', '9:35');
INSERT INTO `lesson_time` (`lesson_num`, `lesson_stime`, `lesson_etime`) VALUES ('2', '9:45', '11:20');
INSERT INTO `lesson_time` (`lesson_num`, `lesson_stime`, `lesson_etime`) VALUES ('3', '11:30', '13:05');
INSERT INTO `lesson_time` (`lesson_num`, `lesson_stime`, `lesson_etime`) VALUES ('4', '13:25', '15:00');
INSERT INTO `lesson_time` (`lesson_num`, `lesson_stime`, `lesson_etime`) VALUES ('5', '15:10', '16:45');
INSERT INTO `lesson_time` (`lesson_num`, `lesson_stime`, `lesson_etime`) VALUES ('6', '16:55', '18:30');
INSERT INTO `lesson_time` (`lesson_num`, `lesson_stime`, `lesson_etime`) VALUES ('7', '18:40', '20:00');
INSERT INTO `lesson_time` (`lesson_num`, `lesson_stime`, `lesson_etime`) VALUES ('8', '20:10', '21:30');
commit;


ALTER TABLE `lesson` 
ADD COLUMN `lesson_num` TINYINT(1) UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Номер пары' AFTER `lesson_date`;



ALTER TABLE `lesson` 
ADD INDEX `fk_lesson_num_idx` (`lesson_num` ASC) VISIBLE;

ALTER TABLE `lesson` 
ADD CONSTRAINT `fk_lesson_num`
  FOREIGN KEY (`lesson_num`)
  REFERENCES `lesson_time` (`lesson_num`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;
  
  
ALTER TABLE `lesson` 
ADD UNIQUE INDEX `UNIQUE_teacher_id_lesson_num` (`teacher_id` ASC, `lesson_date` ASC, `lesson_num` ASC) VISIBLE;


ALTER TABLE `specialty` 
CHANGE COLUMN `specialty_id` `specialty_id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Код напрвления/специальности в БД' ;


ALTER TABLE `stud_group` 
DROP INDEX `fk_group_leader2_idx` ;
ALTER TABLE `stud_group` RENAME INDEX `fk_specialty_id` TO `specialty_id_idx`;
ALTER TABLE `stud_group` ALTER INDEX `specialty_id_idx` VISIBLE;
ALTER TABLE `stud_group` RENAME INDEX `fk_curator_id_idx` TO `curator_id_idx`;
ALTER TABLE `stud_group` ALTER INDEX `curator_id_idx` VISIBLE;
ALTER TABLE `stud_group` RENAME INDEX `fk_group_leader_idx` TO `group_leader_idx`;
ALTER TABLE `stud_group` ALTER INDEX `group_leader_idx` VISIBLE;
ALTER TABLE `stud_group` RENAME INDEX `fk_group_leader2` TO `group_leader2_idx`;
ALTER TABLE `stud_group` ALTER INDEX `group_leader2_idx` VISIBLE;


ALTER TABLE `stud_group` 
ADD CONSTRAINT `fk_specialty_id`
  FOREIGN KEY (`specialty_id`)
  REFERENCES `specialty` (`specialty_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;



CREATE TABLE `work` (
  `work_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `work_code` VARCHAR(16) NOT NULL COMMENT 'Шифр по учебному плану',
  `work_year` YEAR(4) NOT NULL COMMENT 'Учебный год начала выполнения работы',
  `work_semestr_start` TINYINT UNSIGNED NOT NULL COMMENT 'Начальный семестр выполнения работы',
  `work_semestr_end` TINYINT UNSIGNED NOT NULL COMMENT 'Последний семестр выполнения работы',
  `work_type` ENUM('course', 'graduation') NOT NULL COMMENT 'Тип работы: курсовая/выпускная',
  `specialty_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на направление/специальность',
  `work_closed` TINYINT(1) UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Флаг закрытия ведомости с курсовой работой',
  PRIMARY KEY (`work_id`))
COMMENT = 'Курсовые дипломные работы';



ALTER TABLE `work` 
ADD INDEX `fk_specialty_idx` (`specialty_id` ASC) VISIBLE;

ALTER TABLE `work` 
ADD CONSTRAINT `fk_specialty`
  FOREIGN KEY (`specialty_id`)
  REFERENCES `specialty` (`specialty_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;
  
  
ALTER TABLE `work` 
ADD UNIQUE INDEX `UNIQUE` (`work_code` ASC, `work_year` ASC, `specialty_id` ASC, `work_semestr_start` ASC) VISIBLE;



CREATE TABLE `work_student` (
  `work_student_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `work_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на work_id',
  `student_id` BIGINT UNSIGNED NOT NULL COMMENT 'Ссылка на студента',
  `teacher_id` INT UNSIGNED NULL COMMENT 'Ссылка на преподавателя (научного руководителя)',
  `work_theme` VARCHAR(1000) NULL COMMENT 'Тема работы',
  `work_mark` TINYINT(1) UNSIGNED NULL COMMENT 'Оценка по 5-ти балльной шкале (0- неявка, 2,3,4,5)',
  `work_mark_exclude` TINYINT(1) UNSIGNED NULL COMMENT 'Используется для обозначения исключения записи из списка:\n1- студент отчислен\n2- перезачтено',
  PRIMARY KEY (`work_student_id`));


ALTER TABLE `work_student` 
ADD INDEX `UNIQUE` (`work_id` ASC, `student_id` ASC) VISIBLE;

ALTER TABLE `work_student` 
ADD CONSTRAINT `fk_work_id`
  FOREIGN KEY (`work_id`)
  REFERENCES `work` (`work_id`)
  ON DELETE CASCADE
  ON UPDATE NO ACTION;
  
 ALTER TABLE `work_student` 
ADD CONSTRAINT `fk_student_id_`
  FOREIGN KEY (`student_id`)
  REFERENCES `student` (`student_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;
  
  
ALTER TABLE `work_student` 
ADD INDEX `fk_teacher_id_idx` (`teacher_id` ASC) VISIBLE;
;
ALTER TABLE `work_student` 
ADD CONSTRAINT `fk_teacher_id_`
  FOREIGN KEY (`teacher_id`)
  REFERENCES `teacher` (`teacher_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;

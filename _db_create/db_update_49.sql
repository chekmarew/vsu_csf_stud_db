ALTER TABLE `teacher` 
ADD COLUMN `teacher_notify_results_fail` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Уведомлять о высоком проценте неудовлетворительных оценок' AFTER `teacher_dean_staff`;

set sql_safe_updates=0;
update teacher set teacher_notify_results_fail=1 where teacher_dean_staff=1;
commit;


CREATE TABLE `certificate_of_study` (
  `certificate_of_study_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `student_id` BIGINT UNSIGNED NOT NULL COMMENT 'Ссылка на student_id',
  `specialty_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на specialty_id',
  `certificate_of_study_request_time` DATETIME NOT NULL COMMENT 'Дата запроса справки студентом',
  `certificate_of_study_print_time` DATETIME NULL COMMENT 'Дата печати справки',
  `certificate_of_study_ready_time` DATETIME NULL COMMENT 'Дата готовности справки',
  `certificate_of_study_year` YEAR NULL COMMENT 'Год (появляется при print_time)',
  `certificate_of_study_num` INT UNSIGNED NULL COMMENT 'Номер в журнале (появляется при print_time)',
  `certificate_of_study_with_holidays_period` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Указывать в справке каникулярный период',
  `certificate_of_study_with_official_seal` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Требуется гербовая печать',
  PRIMARY KEY (`certificate_of_study_id`))
COMMENT = 'Учёт справок об обучении';


ALTER TABLE `certificate_of_study` 
ADD UNIQUE INDEX `UNIQUE` (`certificate_of_study_year` ASC, `certificate_of_study_num` ASC) VISIBLE;



ALTER TABLE `certificate_of_study` 
ADD INDEX `fk_certificate_of_study_student_id_idx` (`student_id` ASC) VISIBLE,
ADD INDEX `fk_certificate_of_study_specialty_id_idx` (`specialty_id` ASC) VISIBLE;

ALTER TABLE `certificate_of_study` 
ADD CONSTRAINT `fk_certificate_of_study_student_id`
  FOREIGN KEY (`student_id`)
  REFERENCES `student` (`student_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE,
ADD CONSTRAINT `fk_certificate_of_study_specialty_id`
  FOREIGN KEY (`specialty_id`)
  REFERENCES `specialty` (`specialty_id`)
  ON DELETE NO ACTION
  ON UPDATE CASCADE;
  
  
  
ALTER TABLE `certificate_of_study` 
ADD COLUMN `certificate_of_study_surname` VARCHAR(45) NOT NULL AFTER `specialty_id`,
ADD COLUMN `certificate_of_study_firstname` VARCHAR(45) NOT NULL AFTER `certificate_of_study_surname`,
ADD COLUMN `certificate_of_study_middlename` VARCHAR(45) NULL AFTER `certificate_of_study_firstname`,
ADD COLUMN `certificate_of_study_course` TINYINT UNSIGNED NULL AFTER `certificate_of_study_middlename`;


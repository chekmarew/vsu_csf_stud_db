ALTER TABLE `subject` 
CHANGE COLUMN `subject_name` `subject_name` VARCHAR(256) NOT NULL COMMENT 'Наименование предмета с кодом' ;


CREATE TABLE `specialty` (
  `specialty_id` INT NOT NULL AUTO_INCREMENT COMMENT 'Код напрвления/специальности в БД',
  `specialty_code` VARCHAR(16) NOT NULL COMMENT 'Код специальности по классификатору',
  `specialty_name` VARCHAR(256) NOT NULL COMMENT 'Название направления / специальности',
  `specialization` VARCHAR(256) NOT NULL DEFAULT '' COMMENT 'Специализация / профиль',
  `education_level` ENUM('bachelor', 'specialist') NOT NULL DEFAULT 'bachelor' COMMENT 'Уровень образования (бакалавр или специалист)',
  `education_standart` ENUM('fgos3+', 'fgos3++') NOT NULL DEFAULT 'fgos3++' COMMENT 'Образовательный стандарт (ФГОС3+ или ФГОС3++)',
  PRIMARY KEY (`specialty_id`))
COMMENT = 'Направление / специальность';

ALTER TABLE `specialty` 
ADD UNIQUE INDEX `specialty_uk` (`specialty_code` ASC, `specialty_name` ASC, `specialization` ASC, `education_level` ASC, `education_standart` ASC) VISIBLE;



ALTER TABLE `stud_group` 
ADD COLUMN `specialty_id` INT NULL AFTER `stud_group_subnum`;



ALTER TABLE `stud_group` 
CHANGE COLUMN `specialty_id` `specialty_id` INT(11) NULL DEFAULT NULL COMMENT 'Ссылка на специальность specialty(specialty_id)' ,
ADD INDEX `fk_specialty_id_idx` (`specialty_id` ASC) VISIBLE;

ALTER TABLE `stud_group` 
ADD CONSTRAINT `fk_specialty_id`
  FOREIGN KEY (`specialty_id`)
  REFERENCES `specialty` (`specialty_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;


insert into specialty (specialty_code, specialty_name, specialization)

select distinct substr(stud_group_specialty,1,8), substr(stud_group_specialty,10), stud_group_specialization from stud_group order by stud_group_num;

commit;

SET SQL_SAFE_UPDATES = 0;

update stud_group set specialty_id=(select specialty_id from specialty where substr(stud_group.stud_group_specialty,1,8)=specialty.specialty_code and stud_group.stud_group_specialization=specialty.specialization);

commit;



ALTER TABLE `stud_group` 
DROP COLUMN `stud_group_specialization`,
DROP COLUMN `stud_group_specialty`,
CHANGE COLUMN `specialty_id` `specialty_id` INT(11) NOT NULL COMMENT 'Ссылка на специальность specialty(specialty_id)';


ALTER TABLE `admin_user` 
ADD COLUMN `admin_user_email` VARCHAR(45) NULL COMMENT 'E-mail',
ADD COLUMN `admin_user_phone` BIGINT(20) NULL COMMENT 'Сотовый телефон',
ADD COLUMN `admin_user_contacts` VARCHAR(4000) NULL COMMENT 'Доп. контактные данные';

ALTER TABLE `teacher` 
ADD COLUMN `teacher_email` VARCHAR(45) NULL COMMENT 'E-mail',
ADD COLUMN `teacher_phone` BIGINT(20) NULL COMMENT 'Сотовый телефон',
ADD COLUMN `teacher_contacts` VARCHAR(4000) NULL COMMENT 'Доп. контактные данные';

ALTER TABLE `student` 
ADD COLUMN `student_email` VARCHAR(45) NULL COMMENT 'E-mail',
ADD COLUMN `student_phone` BIGINT(20) NULL COMMENT 'Сотовый телефон',
ADD COLUMN `student_contacts` VARCHAR(4000) NULL COMMENT 'Доп. контактные данные';

ALTER TABLE `curriculum_unit_status_hist` 
ADD COLUMN `curriculum_unit_doc` LONGBLOB NULL COMMENT 'ODT-файл ведомости' AFTER `curriculum_unit_status`;




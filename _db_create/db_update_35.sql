ALTER TABLE `specialty` 
ADD COLUMN `education_level_order` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '1 - Бакалавр или специалист, 2 - Магистр' AFTER `department_id`,
CHANGE COLUMN `specialty_id` `specialty_id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Код напрвления/специальности в БД' ,
CHANGE COLUMN `education_level` `education_level` ENUM('bachelor', 'specialist', 'master') CHARACTER SET 'latin1' NOT NULL DEFAULT 'bachelor' COMMENT 'Уровень образования (бакалавр, специалист, магистр)' ;


INSERT INTO `specialty` (`specialty_code`, `specialty_name`, `specialization`, `education_level`, `education_standart`, `department_id`, `education_level_order`, `specialty_active`) VALUES ('09.04.02', 'Информационные системы и технологии', 'Анализ и синтез информационных систем', 'master', 'fgos3++', '1601', '2', '1');
INSERT INTO `specialty` (`specialty_code`, `specialty_name`, `specialization`, `education_level`, `education_standart`, `department_id`, `education_level_order`, `specialty_active`) VALUES ('09.04.02', 'Информационные системы и технологии', 'Системы прикладного искусственного интеллекта', 'master', 'fgos3++', '1605', '2', '1');
INSERT INTO `specialty` (`specialty_code`, `specialty_name`, `specialization`, `education_level`, `education_standart`, `department_id`, `education_level_order`, `specialty_active`) VALUES ('09.04.02', 'Информационные системы и технологии', 'Информационные технологии в менеджменте', 'master', 'fgos3++', '1606', '2', '1');
INSERT INTO `specialty` (`specialty_code`, `specialty_name`, `specialization`, `education_level`, `education_standart`, `department_id`, `education_level_order`, `specialty_active`) VALUES ('09.04.02', 'Информационные системы и технологии', 'Мобильные приложения и компьютерные игры', 'master', 'fgos3++', '1602', '2', '1');
INSERT INTO `specialty` (`specialty_code`, `specialty_name`, `specialization`, `education_level`, `education_standart`, `department_id`, `education_level_order`, `specialty_active`) VALUES ('02.04.01', 'Математика и компьютерные науки', 'Компьютерное моделирование и искусственный интеллект', 'master', 'fgos3++', '1603', '2', '1');
INSERT INTO `specialty` (`specialty_code`, `specialty_name`, `specialization`, `education_level`, `education_standart`, `department_id`, `education_level_order`, `specialty_active`) VALUES ('02.04.01', 'Математика и компьютерные науки', 'Компьютерные науки и информационные технологии для цифровой экономики', 'master', 'fgos3++', '1603', '2', '1');
INSERT INTO `specialty` (`specialty_code`, `specialty_name`, `specialization`, `education_level`, `education_standart`, `department_id`, `education_level_order`, `specialty_active`) VALUES ('09.04.04', 'Программная инженерия', 'Системное программирование', 'master', 'fgos3++', '1602', '2', '1');
commit;



ALTER TABLE `person` 
ADD COLUMN `allow_jwt_auth` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешена авторизация через jwt_token для мобильного приложения';

ALTER TABLE `person_hist` 
ADD COLUMN `allow_jwt_auth` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешена авторизация через jwt_token для мобильного приложения';

ALTER TABLE `subject` CHANGE COLUMN `subject_short_name` `subject_short_name` VARCHAR(48) NULL DEFAULT NULL ;



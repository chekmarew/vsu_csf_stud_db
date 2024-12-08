CREATE TABLE `admin_user` (
  `admin_user_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'ID секретаря',
  `admin_user_surname` varchar(45) NOT NULL COMMENT 'Фамилия секретаря',
  `admin_user_firstname` varchar(45) NOT NULL COMMENT 'Имя секретаря',
  `admin_user_middlename` varchar(45) DEFAULT NULL COMMENT 'Отчество секретаря',
  `admin_user_login` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`admin_user_id`),
  UNIQUE KEY `admin_user_login_UNIQUE` (`admin_user_login`)
) COMMENT='Административный пользователь (секретарь)';


ALTER TABLE `teacher` 
ADD COLUMN `teacher_login` VARCHAR(45) NULL,
ADD UNIQUE INDEX `teacher_login_UNIQUE` (`teacher_login` ASC) VISIBLE;
;

ALTER TABLE `student` 
ADD COLUMN `student_login` VARCHAR(45) NULL,
ADD UNIQUE INDEX `student_login_UNIQUE` (`student_login` ASC) VISIBLE;
;
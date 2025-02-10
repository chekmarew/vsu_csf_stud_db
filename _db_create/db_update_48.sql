CREATE TABLE `auth_code_4_change_email` (
  `auth_code_4_change_email_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `person_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на person(person_id)',
  `email_old` VARCHAR(45) NULL COMMENT 'старый e-mail',
  `email` VARCHAR(45) NOT NULL COMMENT 'новый e-mail',
  `code_old` MEDIUMINT UNSIGNED NULL COMMENT 'Код, отправленный на старый e-mail',
  `code` MEDIUMINT UNSIGNED NOT NULL COMMENT 'Код, отправленный на новый e-mail',
  `code_send_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Время отправки кода',
  `code_accept_time` DATETIME NULL COMMENT 'Время принятия кода',
  `auth_err_count` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Количество ошибок ввода кода',
  PRIMARY KEY (`auth_code_4_change_email_id`))
COMMENT = 'коды для смены e-mail';




ALTER TABLE `auth_code_4_change_email` 
ADD INDEX `fk_person_id_idx` (`person_id` ASC) VISIBLE;
ALTER TABLE `auth_code_4_change_email` 
ADD CONSTRAINT `fk_auth_code_4_change_email_person_id`
  FOREIGN KEY (`person_id`)
  REFERENCES `person` (`person_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;
  
  
  
CREATE TABLE `auth_code_4_change_phone` (
  `auth_code_4_change_phone_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `person_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на person(person_id)',
  `phone_old` BIGINT UNSIGNED NULL COMMENT 'старый номер телефона',
  `phone` BIGINT UNSIGNED NOT NULL COMMENT 'новый номер телефона',
  `code_old` MEDIUMINT UNSIGNED NULL COMMENT 'Код, отправленный на старый номер телефона',
  `code` MEDIUMINT UNSIGNED NOT NULL COMMENT 'Код, отправленный на новый номер телефона',
  `code_send_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Время отправки кода',
  `code_accept_time` DATETIME NULL COMMENT 'Время принятия кода',
  `auth_err_count` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Количество ошибок ввода кода',
  PRIMARY KEY (`auth_code_4_change_phone_id`))
COMMENT = 'коды для смены номера телефона';


ALTER TABLE `auth_code_4_change_phone` 
ADD INDEX `fk_person_id_idx` (`person_id` ASC) VISIBLE;
ALTER TABLE `auth_code_4_change_phone` 
ADD CONSTRAINT `fk_auth_code_4_change_phone_person_id`
  FOREIGN KEY (`person_id`)
  REFERENCES `person` (`person_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;
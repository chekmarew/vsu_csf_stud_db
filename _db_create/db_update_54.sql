ALTER TABLE `specialty` 
ADD COLUMN `semestr_distirib` TINYINT(3) UNSIGNED NULL COMMENT 'Семестр в котором будет распределение по специализациям.профилям' AFTER `parent_specialty_id`,
ADD COLUMN `semestr_end` TINYINT(3) UNSIGNED NULL COMMENT 'Последний семестр обучения' AFTER `semestr_distirib`;


UPDATE `specialty` SET `semestr_end` = '10' WHERE (`specialty_id` = '1');
UPDATE `specialty` SET `semestr_end` = '11' WHERE (`specialty_id` = '16');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '17');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '18');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '19');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '20');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '21');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '22');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '24');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '25');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '26');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '27');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '28');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '29');
UPDATE `specialty` SET `semestr_distirib` = '3', `semestr_end` = '8' WHERE (`specialty_id` = '30');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '31');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '32');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '33');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '34');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '35');
UPDATE `specialty` SET `semestr_distirib` = '5', `semestr_end` = '8' WHERE (`specialty_id` = '37');
UPDATE `specialty` SET `semestr_end` = '11' WHERE (`specialty_id` = '38');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '39');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '40');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '41');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '42');
UPDATE `specialty` SET `semestr_end` = '4' WHERE (`specialty_id` = '43');
UPDATE `specialty` SET `semestr_end` = '4' WHERE (`specialty_id` = '44');
UPDATE `specialty` SET `semestr_end` = '4' WHERE (`specialty_id` = '45');
UPDATE `specialty` SET `semestr_end` = '4' WHERE (`specialty_id` = '46');
UPDATE `specialty` SET `semestr_end` = '4' WHERE (`specialty_id` = '47');
UPDATE `specialty` SET `semestr_end` = '4' WHERE (`specialty_id` = '48');
UPDATE `specialty` SET `semestr_end` = '4' WHERE (`specialty_id` = '49');
UPDATE `specialty` SET `semestr_end` = '8' WHERE (`specialty_id` = '50');
UPDATE `specialty` SET `semestr_distirib` = '5', `semestr_end` = '8' WHERE (`specialty_id` = '51');
UPDATE `specialty` SET `semestr_end` = '11' WHERE (`specialty_id` = '52');
UPDATE `specialty` SET `semestr_distirib` = '3', `semestr_end` = '8' WHERE (`specialty_id` = '54');
UPDATE `specialty` SET `semestr_end` = '4' WHERE (`specialty_id` = '55');
commit;
ALTER TABLE `specialty` 
CHANGE COLUMN `semestr_end` `semestr_end` TINYINT(3) UNSIGNED NOT NULL COMMENT 'Последний семестр обучения' ;


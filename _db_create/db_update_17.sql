ALTER TABLE `department` 
ADD COLUMN `department_name_short` VARCHAR(16) NULL AFTER `department_name`,
ADD UNIQUE INDEX `department_name_short_UNIQUE` (`department_name_short`);

ALTER TABLE `specialty` 
ADD COLUMN `department_id` INT UNSIGNED NOT NULL DEFAULT 1600 COMMENT 'Ссылка на кафедру' AFTER `education_standart`,
ADD INDEX `fk_department_id_idx` (`department_id`) ;
;
ALTER TABLE `specialty` 
ADD CONSTRAINT `fk_department_id`
  FOREIGN KEY (`department_id`)
  REFERENCES `department` (`department_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;
  
update department set department_name_short='ФКН' where department_id=1600;
update department set department_name_short='ИС' where department_id=1601;
update department set department_name_short='ПиИТ' where department_id=1602;
update department set department_name_short='ЦТ' where department_id=1603;
update department set department_name_short='ТОиЗИ' where department_id=1605;
update department set department_name_short='ИТУ' where department_id=1606;
commit;


set SQL_SAFE_UPDATES=0;
update specialty set department_id=1602 where specialty_code='09.03.04';
update specialty set department_id=1603 where specialty_code='02.03.01';
update specialty set department_id=1605 where specialty_code in ('10.05.01', '10.03.01');
update specialty set department_id=1606 where specialty_code = '09.03.03';

update specialty set department_id=1601 where specialty_code='09.03.02' and specialization in ('Информационные системы в телекоммуникациях','Информационные системы и сетевые технологии');
update specialty set department_id=1605 where specialty_code='09.03.02' and specialization='Обработка информации и машинное обучение';
update specialty set department_id=1606 where specialty_code='09.03.02' and specialization='Информационные системы и технологии в управлении предприятием';
update specialty set department_id=1602 where specialty_code='09.03.02' and specialization='Программная инженерия в информационных системах';
commit;



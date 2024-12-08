ALTER TABLE `person` 
ADD COLUMN `gender` ENUM('M', 'W') NULL COMMENT 'Пол',
ADD COLUMN `birthday` DATE NULL COMMENT 'Дата рождения';

set sql_safe_updates=0;
update person set gender='W' where middlename like '%на';
update person set gender='M' where middlename like '%ич';
commit;
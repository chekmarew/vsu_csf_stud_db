ALTER TABLE `specialty` 
ADD COLUMN `specialty_active` TINYINT(1) NOT NULL DEFAULT 1;

set sql_safe_updates=0;

update specialty set specialty_active=0 where education_standart='fgos3+' and specialty_code not in ('10.05.01','10.03.01');
commit;
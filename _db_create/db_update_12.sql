SET SQL_SAFE_UPDATES = 0;
update curriculum_unit set curriculum_unit_code= curriculum_unit_id  where curriculum_unit_code ='0';
commit;

ALTER TABLE `curriculum_unit` 
ADD UNIQUE INDEX `UNIQUE_stud_group_id_code` (`stud_group_id`, `curriculum_unit_code`);


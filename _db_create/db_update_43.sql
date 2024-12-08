ALTER TABLE `att_mark` 
ADD COLUMN `attendance_rate_cached` DECIMAL(5,4) UNSIGNED NULL COMMENT 'Кэшированное значение отношение количества посещенных занятий к общему числу занятий для closed curriculum_unit' AFTER `att_mark_append_ball`;

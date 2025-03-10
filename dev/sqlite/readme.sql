select distinct
                zp.zi
                , zp.zi_left_up
                , zp.zi_left
                , zp.zi_left_down
                , zp.zi_up
                , zp.zi_mid
                , zp.zi_down
                , zp.zi_right_up
                , zp.zi_right
                , zp.zi_right_down
                , zp.zi_mid_out
                , zp.zi_mid_in
            from t_zi_part zp
            where 1=1
                and zp.is_active = 'Y'
                and (
                       trim(zp.zi_left_up) = '差'
                    OR trim(zp.zi_left) = '差'
                    OR trim(zp.zi_left_down) = '差'
                    OR trim(zp.zi_up) = '差'
                    OR trim(zp.zi_mid) = '差'
                    OR trim(zp.zi_down) = '差'
                    OR trim(zp.zi_right_up) = '差'
                    OR trim(zp.zi_right) = '差'
                    OR trim(zp.zi_right_down) = '差'
                    OR trim(zp.zi_mid_out) = '差'
                    OR trim(zp.zi_mid_in) = '差'
                )
            order by zp.zi
             limit 20
            ;


-- alter table t_ele_zi add column is_neted CHAR(1) CHECK (is_neted IS NULL OR is_neted = 'Y');

create table t_ele_zi_bkup1 as select * from t_ele_zi;

select * from t_part where is_active='Y' order by zi;
select * from t_ele_zi where is_active='Y' order by zi;

select * from t_ele_zi where n_frequency = 0;
select * from t_ele_zi where u_id in (348,7747);

select * from t_ele_zi where zi = '宁';
select * from t_zi where zi = '宁';
--delete from t_ele_zi where zi is null;

update t_ele_zi set n_frequency=10 where zi = '禺'

select * from t_ele_zi where u_id in (431, 432, 435, 434, 437);
delete from t_ele_zi where u_id in (431, 432, 435, 434, 437);

create table t_ele_zi as 
select 
zi, is_zi, id_kangxi, meaning, pinyin, n_strokes, term, examples, variant, n_frequency, category, sub_category, notes, u_id, is_active, is_radical, phono, ts
from t_ele_zi_bkup1;

alter table t_ele_zi add column is_neted CHAR(1) CHECK (is_neted IS NULL OR is_neted in ('', 'Y'));

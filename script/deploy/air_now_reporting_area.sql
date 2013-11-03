CREATE TABLE air_canary.air_now_reporting_area (
    valid_date date not null,
    valid_time time not null,
    issue_date date,
    time_zone char(3),
    record_sequence tinyint(1),
    data_type char(1),
    is_primary char(1),
    reporting_area varchar(45) not null,
    state_code char(2),
    latitude varchar(7),
    longitude varchar(9),
    parameter_name varchar(10) not null,
    aqi_value smallint unsigned,
    aqi_category varchar(40),
    action_day varchar(3),
    discussion varchar(500),
    forecast_source varchar(100),
    primary key (valid_date, valid_time, issue_date, reporting_area, parameter_name, state_code),
    index (reporting_area, parameter_name),
    index (parameter_name),
    index (latitude, longitude)
) engine innodb;
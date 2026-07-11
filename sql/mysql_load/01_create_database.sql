-- Phase 6: Load to MySQL
-- Script 01: Create database

CREATE DATABASE IF NOT EXISTS automated_data_quality_etl;

USE automated_data_quality_etl;
-- Phase 6: Load to MySQL
-- Script 02: Create table for feature-engineered Online Retail data

USE automated_data_quality_etl;

DROP TABLE IF EXISTS online_retail_feature_engineered;

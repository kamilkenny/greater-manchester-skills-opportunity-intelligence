/*
GM SkillsFlow
Migration 003: Upgrade initial Gold snapshot dimensions

Purpose:
Replace the three provisional snapshot dimensions created during the
initial Silver-to-Gold load so the governed dimensional model can create
the new SCD2-ready structures.

Fact, control, audit and history tables are intentionally untouched.
*/

DROP TABLE IF EXISTS [dim].[borough];
DROP TABLE IF EXISTS [dim].[mbacc_gateway];
DROP TABLE IF EXISTS [dim].[ssa_subject];

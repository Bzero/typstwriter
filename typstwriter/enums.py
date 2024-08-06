import enum

compiler_mode = enum.Enum("compiler_mode", ["on_demand", "live"])
search_mode = enum.Enum("search_mode", ["case_insensitive", "case_sensitive", "whole_words", "regex"])
search_direction = enum.Enum("search_direction", ["next", "previous"])

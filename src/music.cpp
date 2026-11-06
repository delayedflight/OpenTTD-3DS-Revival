/* $Id$ */

/** @file music.cpp The songs that OpenTTD knows. */

#include "stdafx.h"
#include "music.h"

#ifdef N3DS
#define MUSIC_FILE(name) name ".wav"
#else
#define MUSIC_FILE(name) name ".gm"
#endif

const SongSpecs _origin_songs_specs[] = {
	{MUSIC_FILE("gm_tt00"), "Tycoon DELUXE Theme"},
	{MUSIC_FILE("gm_tt02"), "Easy Driver"},
	{MUSIC_FILE("gm_tt03"), "Little Red Diesel"},
	{MUSIC_FILE("gm_tt17"), "Cruise Control"},
	{MUSIC_FILE("gm_tt07"), "Don't Walk!"},
	{MUSIC_FILE("gm_tt09"), "Fell Apart On Me"},
	{MUSIC_FILE("gm_tt04"), "City Groove"},
	{MUSIC_FILE("gm_tt19"), "Funk Central"},
	{MUSIC_FILE("gm_tt06"), "Stoke It"},
	{MUSIC_FILE("gm_tt12"), "Road Hog"},
	{MUSIC_FILE("gm_tt05"), "Aliens Ate My Railway"},
	{MUSIC_FILE("gm_tt01"), "Snarl Up"},
	{MUSIC_FILE("gm_tt18"), "Stroll On"},
	{MUSIC_FILE("gm_tt10"), "Can't Get There From Here"},
	{MUSIC_FILE("gm_tt08"), "Sawyer's Tune"},
	{MUSIC_FILE("gm_tt13"), "Hold That Train!"},
	{MUSIC_FILE("gm_tt21"), "Movin' On"},
	{MUSIC_FILE("gm_tt15"), "Goss Groove"},
	{MUSIC_FILE("gm_tt16"), "Small Town"},
	{MUSIC_FILE("gm_tt14"), "Broomer's Oil Rag"},
	{MUSIC_FILE("gm_tt20"), "Jammit"},
	{MUSIC_FILE("gm_tt11"), "Hard Drivin'"},
};

assert_compile(NUM_SONGS_AVAILABLE == lengthof(_origin_songs_specs));

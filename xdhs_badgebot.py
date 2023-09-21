#!/usr/bin/python3 -u
################################################################################
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# # OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>
################################################################################

import pkg_resources
pkg_resources.require("discord.py==1.7.3")
import discord

import os
import datetime
import logging
import server
import database
import math
from discord.ext import commands, tasks
import mysql.connector
import time
from config import config

DISCORD_TOKEN = config['DISCORD']['TOKEN']

BOT_COMMANDS_CHANNEL_NAME = "bot-commands"  # Used by XDHS-Team and BadgeBot
BOT_COMMANDS_CHANNEL_ID = 753637350877429842
BOT_SPAM_CHANNEL_NAME = "🤖-bot-spam"  #  Used by members for ?stats and ?badges
POD_1_MIN = 45  # Minimum win rate threshold required for pod 1 role
POD_2_MAX = 55  # Maximum win rate threshold allowed for pod 2 role
DAY_OF_MONTH_TO_CHECK_POD_ROLES = 1
XDHS_GUILD_ID = 528728694680715324

logging.basicConfig(level=logging.INFO, filename=config['LOGGING']['PATH'], filemode='a+', format='%(asctime)s [%(levelname)s] : %(message)s', encoding='utf-8')

logging.info(discord.version_info)

# An overridden version of the Bot class that will listen to other bots. Without this override this bot would ignore the ?role commands from RoleBot.
class UnfilteredBot(commands.Bot):
	async def process_commands(self, message):
		ctx = await self.get_context(message)
		await self.invoke(ctx)


bot = UnfilteredBot(command_prefix='?')


# Catch 'command not found' errors and check for ?commandlist commands. Note to anyone reading this: Yes, this is how I did it. No, I will not be taking questions!
@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, discord.ext.commands.CommandNotFound):
		# Command was not found - check if the command is a custom command from the spreadsheet.
		command_name = str(error).split('"')[1::2][0]  # Extract the command name from the exception string
		command = database.get_command_by_name(command_name)
		if command is not None:
			# Check for XDHS Team role requirement
			is_allowed = False
			if command[0] is True:
				if 'XDHS Team' in str(ctx.author.roles) or 'Host' in str(ctx.author.roles):
					is_allowed = True
			else:
				is_allowed = True

			if is_allowed is True:
				return await ctx.channel.send(command[1])
			else:
				return await ctx.channel.send("Only XDHS Team members can use this command.")

	await ctx.channel.send(error)


@bot.event
async def on_ready():
	logging.info(F"Bot online and ready")
	logging.debug(F"{bot.guilds}")


@bot.event
async def on_message(message):
# 885125305461784626 = this bot
# 1073143753428172881 = EventBot
	if message.author.id != 885125305461784626 and message.author.id != 1073143753428172881 and (message.channel.id == 907524659099099178 or message.channel.id == 753639027428687962): # First is test server, second is XDHS
		if message.type == discord.MessageType.default:
			pod1_emoji = discord.utils.get(message.guild.emojis, name="Pod1")
			pod2_emoji = discord.utils.get(message.guild.emojis, name="Pod2")
			#pod3_emoji = discord.utils.get(message.guild.emojis, name="Pod3")
			await message.add_reaction(pod1_emoji)
			await message.add_reaction(pod2_emoji)
			#await message.add_reaction(pod3_emoji)
	else:
		await bot.process_commands(message)


"""
@bot.event
async def on_member_remove(member):
	channel = bot.get_channel(BOT_COMMANDS_CHANNEL_ID)
	await channel.send(F"{member} has left the server.")
"""

class TeamCommands(commands.Cog, name="Team Commands"):
	"""Commands usable only by team members"""
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None  # TODO: What's this?

	# UNFINISHED!
	# The idea was to add a shark emoji to the nicknames of members with the shark role but some thought this would encourage too much spikey behaviour...
	@commands.command(name='shark', brief="", help="<member name>", hidden=True)
	@commands.has_permissions(change_nickname=True)
	async def shark(self, ctx, member: discord.Member):
		if ctx.channel.id != discord.utils.get(ctx.guild.channels, name=BOT_COMMANDS_CHANNEL_NAME).id:
			return

		# TODO: Check for empty nick first, in case it is "none"
		await member.edit(nick=(F"{member.nick} 🦈"))
		return


	# When RoleBot sends a ?role command this removes/applies the role.
	@commands.command(name='role', brief="Add or delete a role from a member.", help= "<verb> - add or del\n<role> - The role to add or delete (case sensitive)\n<member> - The member to change (case sensitive)", hidden=True)
	async def role(self, ctx, verb: str, role: discord.Role, member: discord.Member):
		if ctx.channel.id != discord.utils.get(ctx.guild.channels, name=BOT_COMMANDS_CHANNEL_NAME).id:
			#await ctx.send(F"Use #{BOT_COMMANDS_CHANNEL_NAME} channel not #{ctx.channel.name}")
			return

		if verb == "add":
			await member.add_roles(role)
			await ctx.send(F"Added {role} to {member}.")
			return
		elif verb == "del":
			await member.remove_roles(role)
			await ctx.send(F"Deleted {role} from {member}.")
			return
		else:
			await ctx.send(F"unknown <verb> \"{verb}\" - use \"add\" or \"del\"")


class MemberCommands(commands.Cog, name='Member Commands'):
	"""Commands usable by all members"""
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None  # TODO: What's this?

	@commands.command(name='TandEm', hidden=True)
	async def tandem(self, ctx):
		await ctx.send("https://melmagazine.com/wp-content/uploads/2021/01/66f-1.jpg")  # hehehe

	@commands.command(name='badges', brief='Show your badge card for all to see.', help= 'Your badge card is updated during the badge update of your most recent draft.')
	async def badges(self, ctx):
		if ctx.channel.id != discord.utils.get(ctx.guild.channels, name=BOT_SPAM_CHANNEL_NAME).id:
			#await ctx.send(F"Use #{BOT_SPAM_CHANNEL_NAME} channel not #{ctx.channel.name}")
			return

		#if ctx.message.author.id == self.id:
		#  return

		discord_id = ctx.message.author.id
		badges = database.get_badge_card(discord_id)
		if badges is None:
			await ctx.send(F"No badge card found for {ctx.message.author.name}.")
			return

		url = badges[0]
		timestamp = badges[1]

		embed = discord.Embed()
		embed.set_image(url=url)
		embed.timestamp = datetime.datetime.fromtimestamp(timestamp)
		embed.set_footer(text=F"Last updated", icon_url="https://i.imgur.com/NPtgFpC.png") # TODO: The url for this icon should be a variable 'cause it's used in a few places.
		await ctx.send(embed=embed)

	@commands.command(name='pmbadges', brief='View your badge card via private message.', help= 'Your badge card is updated during the badge update of your most recent draft.')
	async def pmbadges(self, ctx):
		if ctx.channel.id != discord.utils.get(ctx.guild.channels, name=BOT_SPAM_CHANNEL_NAME).id:
				#await ctx.send(F"Use #{BOT_SPAM_CHANNEL_NAME} channel not #{ctx.channel.name}")
			return

		#if ctx.message.author.id == self.id:
		#  return

		discord_id = ctx.message.author.id
		badges = database.get_badge_card(discord_id)
		if badges is None:
			await ctx.send(F"No badge card found for {ctx.message.author.name}.")
			return

		await ctx.send(F"{ctx.message.author.name}, your badge card will be delivered via private message.")

		url = badges[0]
		timestamp = badges[1]

		embed = discord.Embed()
		embed.set_image(url=url)
		embed.timestamp = datetime.datetime.fromtimestamp(timestamp)
		embed.set_footer(text=F"Last updated", icon_url="https://i.imgur.com/NPtgFpC.png")
		await ctx.message.author.send(embed=embed)

	@commands.command(name='stats', brief='Get your XDHS stats via private message', help='Your stats may take a few hours after a draft ends to update.')
	async def stats(self, ctx):
		if ctx.channel.id != discord.utils.get(ctx.guild.channels, name=BOT_SPAM_CHANNEL_NAME).id:
			#await ctx.send(F"Use #{BOT_SPAM_CHANNEL_NAME} channel not #{ctx.channel.name}")
			return

		#if ctx.message.author.id == self.id:
		#  return

		discord_id = ctx.message.author.id
		stats = database.get_stats(discord_id)
		print(F"stats for {discord_id}: {stats}")
		if stats is None:
			await ctx.send(F"No stats found for {ctx.message.author.name}. You must complete at least one XDHS league/bonus draft or wait a few hours after your first draft for your stats to be available.")
			return

		await ctx.send(F"{ctx.message.author.name}, your stats will be delivered via private message.")

		embed = discord.Embed()
		embed.title = F"Hello, {ctx.message.author.name}! Here are your XDHS stats."

		embed.add_field(name='Devotion Badge', value=stats[1], inline=True)
		embed.add_field(name='Devotion Points', value=stats[2], inline=True)
		embed.add_field(name='Points needed for next badge', value=stats[3], inline=True)

		embed.add_field(name='Victory Badge', value=stats[4], inline=True)
		embed.add_field(name='Victory Points', value=stats[5], inline=True)
		embed.add_field(name='Points needed for next badge', value=stats[6], inline=True)

		embed.add_field(name="Trophy Badge", value=stats[7], inline=True)
		embed.add_field(name="Trophy Points", value=stats[8], inline=True)
		embed.add_field(name="Points needed for next badge", value=stats[9], inline=True)

		embed.add_field(name="Shark Badge", value=stats[10], inline=True)
		embed.add_field(name="Shark Kills", value=stats[11], inline=True)
		embed.add_field(name="Kills needed for next badge", value=stats[12], inline=True)

		embed.add_field(name="Draft Hero Badge", value=stats[13], inline=True)
		embed.add_field(name="Hero Points", value=stats[14], inline=True)
		embed.add_field(name="Points needed for next badge", value=stats[15], inline=True)

		# Recent win rate
		win_rate_recent_league_string = (str(stats[16]) + '%') if stats[16] > 0.0 else "-"
		win_rate_recent_bonus_string = (str(stats[17]) + '%') if stats[17] > 0.0 else "-"
		win_rate_recent_overall_string = (str(stats[18]) + '%') if stats[18] > 0.0 else "-"

		embed.add_field(name='Chrono win rate (last 6 seasons)', value=win_rate_recent_league_string, inline=True)
		embed.add_field(name='Bonus win rate (last 6 seasons)', value=win_rate_recent_bonus_string, inline=True)
		embed.add_field(name='Overall win rate (last 6 seasons)', value=win_rate_recent_overall_string, inline=True)

		# All time win rate
		win_rate_all_time_league_string = (str(stats[19]) + '%') if stats[19] > 0.0 else "-"
		win_rate_all_time_bonus_string = (str(stats[20]) + '%') if stats[20] > 0.0 else "-"
		win_rate_all_time_overall_string = (str(stats[21]) + '%') if stats[21] > 0.0 else "-"

		embed.add_field(name='Chrono win rate (all time)', value=win_rate_all_time_league_string, inline=True)
		embed.add_field(name='Bonus win rate (all time)', value=win_rate_all_time_bonus_string, inline=True)
		embed.add_field(name='Overall win rate (all time)', value=win_rate_all_time_overall_string, inline=True)

		win_rate_recent_overall_value = float(stats[18])
		valid_pods = ""
		if win_rate_recent_overall_value > POD_2_MAX:
			valid_pods = "Pod 1"
		elif win_rate_recent_overall_value < POD_1_MIN:
			valid_pods = "Pod 2"
		else:
			valid_pods = "Pod 1 or 2"

		desired = stats[22]
		assigned = stats[23]

		embed.timestamp = datetime.datetime.fromtimestamp(stats[0])
		embed.set_footer(text=F"Last updated", icon_url="https://i.imgur.com/NPtgFpC.png")

		await ctx.message.author.send(embed=embed)
		return


server.start_server()  # Start the web server before the bot

bot.add_cog(TeamCommands(bot))
bot.add_cog(MemberCommands(bot))

bot.run(DISCORD_TOKEN)

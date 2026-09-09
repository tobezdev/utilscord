from io import BytesIO

import aiohttp

from discord import IntegrationType, InteractionContextType, Bot, ApplicationContext, InputTextStyle, SelectOption, CheckboxGroupOption, Interaction, File, MediaGalleryItem
from discord.ext.commands import Cog

from cogs.premium_handler import premium_cooldown
from discord.commands import SlashCommandGroup
from discord.ui import DesignerModal, Label, InputText, CheckboxGroup, Select, DesignerView, Container, MediaGallery, ActionRow, Button, TextDisplay
from discord.components import MediaGallery as MediaGalleryComponent


class RenderLatexModal(DesignerModal):
	def __init__(self):
		super().__init__(title="Render LaTeX Code")

		self.latex_input = InputText(
			style=InputTextStyle.long,
			placeholder="Enter your LaTeX code",
			required=True,
		)
		self.image_width = InputText(
			placeholder="Image width in pixels",
			required=False,
		)
		self.image_height = InputText(
			placeholder="Image height in pixels",
			required=False,
		)
		self.render_options = CheckboxGroup(
			options=[
				CheckboxGroupOption(label="Use white text (default black)", value="white_text", default=False),
				CheckboxGroupOption(label="Disable background transparency", value="disable_transparency", default=False),
			],
			min_values=0,
			max_values=2,
			required=False,
		)
		self.file_type = Select(
			options=[
				SelectOption(label="PNG", value="png", default=True),
				SelectOption(label="SVG", value="svg"),
			],
			min_values=1,
			max_values=1,
			required=True,
		)

		self.add_item(Label("LaTeX code", self.latex_input))
		self.add_item(Label("Image width (optional)", self.image_width))
		self.add_item(Label("Image height (optional)", self.image_height))
		self.add_item(Label("Rendering options", self.render_options))
		self.add_item(Label("File type", self.file_type))

	async def callback(self, interaction: Interaction):
		render_options = self.render_options.values or []
		file_type = (self.file_type.values or ["png"])[0]
		params = {
			"white": str("white_text" in render_options).lower(),
			"disable_transparency": str("disable_transparency" in render_options).lower(),
		}
		for name, field in (("width", self.image_width), ("height", self.image_height)):
			value = (field.value or "").strip()
			if value:
				try:
					dimension = int(value)
				except ValueError:
					dimension = 0
				if not 1 <= dimension <= 5000:
					await interaction.response.send_message(
						f"Image {name} must be a whole number between 1 and 5000 pixels.",
						ephemeral=True,
					)
					return
				params[name] = str(dimension)

		await interaction.response.defer()
		images = {}
		try:
			async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
				for format_name in dict.fromkeys((file_type, "png")):
					async with session.post(
						f"https://laas.vercel.app/api/{format_name}",
						params=params,
						data=(self.latex_input.value or "").encode("utf-8"),
						headers={"Content-Type": "text/plain; charset=utf-8"},
					) as response:
						response.raise_for_status()
						expected_type = "image/png" if format_name == "png" else "image/svg+xml"
						if response.content_type != expected_type:
							raise ValueError("The renderer did not return an image")
						images[format_name] = await response.read()
		except (aiohttp.ClientError, TimeoutError, ValueError):
			await interaction.followup.send(
				"Couldn't render that LaTeX. Check your code and try again.",
				ephemeral=True,
			)
			return

		container = Container(
			TextDisplay("### Rendered LaTeX"),
			MediaGallery(MediaGalleryItem(url="attachment://latex.png")),
		)
		view = DesignerView(timeout=None)
		view.add_item(container)
		files = [File(BytesIO(data), filename=f"latex.{extension}") for extension, data in images.items()]
		try:
			message = await interaction.followup.send(view=view, files=files, wait=True)
		finally:
			for file in files:
				file.close()
		# SVG is an unreferenced attachment; the PNG URL is returned in the gallery.
		image_url = next(
			(attachment.url for attachment in message.attachments if attachment.filename == f"latex.{file_type}"),
			None,
		)
		if image_url is None and file_type == "png":
			image_url = next(
				(
					item.media.url
					for parent in message.components
					for component in getattr(parent, "walk_components", lambda: ())()
					if isinstance(component, MediaGalleryComponent)
					for item in component.items
					if item.media.url.startswith("https://")
				),
				None,
			)
		if image_url is None:
			await interaction.followup.send(
				"The image was rendered, but its browser link is unavailable. Please try rendering again.",
				ephemeral=True,
			)
			return
		container.add_item(ActionRow(Button(label="View in browser", url=image_url)))
		await message.edit(view=view)


class LaTeX(Cog):
	def __init__(self, bot: Bot) -> None:
		self.bot = bot

	latex = SlashCommandGroup(
		"latex", "LaTeX commands",
		integration_types={IntegrationType.guild_install, IntegrationType.user_install},
		contexts={
			InteractionContextType.guild,
			InteractionContextType.bot_dm,
			InteractionContextType.private_channel,
		},
	)

	@latex.command(name="render", description="Render LaTeX code into an image.")
	@premium_cooldown(normal=900, premium=180)
	async def render_latex(self, ctx: ApplicationContext):
		return await ctx.response.send_modal(RenderLatexModal())


def setup(bot: Bot):
    bot.add_cog(LaTeX(bot))

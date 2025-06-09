from typing import List

def normalize_club_name(name: str) -> str:
    """Normalize club name for comparison by removing accents and converting to lowercase."""
    import unicodedata
    # Remove accents
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    # Convert to lowercase and remove extra spaces
    return ' '.join(name.lower().split())

async def handle_club_selection(self, interaction: discord.Interaction, user_id: int, selected_club: str) -> bool:
    """Handle club selection with normalized comparison."""
    try:
        # Get available clubs
        clubs = await get_clubs()
        logger.info(f"Retrieved clubs from database: {clubs}")
        
        # Normalize the selected club name
        normalized_selected = normalize_club_name(selected_club)
        logger.info(f"Normalized selected club: {normalized_selected}")
        
        # Get available club IDs (normalized)
        available_club_ids = [normalize_club_name(club['club_id']) for club in clubs]
        logger.info(f"Available club_ids (normalized): {available_club_ids}")
        
        # Find the matching club
        matching_club = None
        for club in clubs:
            if normalize_club_name(club['club_id']) == normalized_selected:
                matching_club = club
                break
        
        if not matching_club:
            logger.warning(f"Invalid club selection: {selected_club}")
            await interaction.response.send_message(
                "❌ Clube inválido. Por favor, selecione um dos clubes disponíveis.",
                ephemeral=True
            )
            return False
            
        # Update user's club
        success = await update_user_club(user_id, matching_club['club_id'])
        if not success:
            await interaction.response.send_message(
                "❌ Erro ao atualizar seu clube. Por favor, tente novamente.",
                ephemeral=True
            )
            return False
            
        await interaction.response.send_message(
            f"✅ Clube atualizado com sucesso! Você agora é membro do {matching_club['name']}.",
            ephemeral=True
        )
        return True
        
    except Exception as e:
        logger.error(f"Error in handle_club_selection: {e}")
        await interaction.response.send_message(
            "❌ Ocorreu um erro ao processar sua seleção. Por favor, tente novamente.",
            ephemeral=True
        )
        return False

@club_selection.error
async def club_selection_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handle errors in club selection."""
    logger.error(f"Error in club selection: {error}")
    await interaction.response.send_message(
        "❌ Ocorreu um erro ao processar sua seleção. Por favor, tente novamente.",
        ephemeral=True
    )

@club_selection.autocomplete('clube')
async def club_selection_autocomplete(
    self,
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    """Autocomplete for club selection."""
    try:
        # Get available clubs
        clubs = await get_clubs()
        logger.info(f"Retrieved clubs for autocomplete: {clubs}")
        
        # Normalize the current input
        normalized_current = normalize_club_name(current)
        logger.info(f"Normalized current input: {normalized_current}")
        
        # Filter and sort clubs
        choices = []
        for club in clubs:
            normalized_name = normalize_club_name(club['name'])
            if normalized_current in normalized_name:
                choices.append(app_commands.Choice(name=club['name'], value=club['club_id']))
        
        # Sort choices by name
        choices.sort(key=lambda x: x.name)
        logger.info(f"Generated choices: {choices}")
        
        return choices[:25]  # Discord has a limit of 25 choices
    except Exception as e:
        logger.error(f"Error in club selection autocomplete: {e}")
        return []

@club_selection.command(name="selecionar")
async def select_club(self, interaction: discord.Interaction, clube: str):
    """Select a club to join."""
    try:
        user_id = str(interaction.user.id)
        logger.info(f"User {user_id} selected club_id: {clube}")
        
        # Get available clubs
        clubs = await get_clubs()
        logger.info(f"Retrieved clubs from database: {clubs}")
        
        # Normalize the selected club name
        normalized_selected = normalize_club_name(clube)
        logger.info(f"Normalized selected club: {normalized_selected}")
        
        # Get available club IDs (normalized)
        available_club_ids = [normalize_club_name(club['club_id']) for club in clubs]
        logger.info(f"Available club_ids (normalized): {available_club_ids}")
        
        # Find the matching club
        matching_club = None
        for club in clubs:
            if normalize_club_name(club['club_id']) == normalized_selected:
                matching_club = club
                break
        
        if not matching_club:
            logger.warning(f"Invalid club selection: {clube}")
            await interaction.response.send_message(
                "❌ Clube inválido. Por favor, selecione um dos clubes disponíveis.",
                ephemeral=True
            )
            return
            
        # Update user's club
        success = await update_user_club(user_id, matching_club['club_id'])
        if not success:
            await interaction.response.send_message(
                "❌ Erro ao atualizar seu clube. Por favor, tente novamente.",
                ephemeral=True
            )
            return
            
        await interaction.response.send_message(
            f"✅ Clube atualizado com sucesso! Você agora é membro do {matching_club['name']}.",
            ephemeral=True
        )
        
    except Exception as e:
        logger.error(f"Error in select_club: {e}")
        await interaction.response.send_message(
            "❌ Ocorreu um erro ao processar sua seleção. Por favor, tente novamente.",
            ephemeral=True
        ) 
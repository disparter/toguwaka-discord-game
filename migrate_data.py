from typing import List, Dict, Any

def distribute_data(table_name: str, items: List[Dict[str, Any]]) -> None:
    """Distribute data from AcademiaTokugawa table to specialized tables."""
    logger.info(f"Distributing {len(items)} items from {table_name}")
    
    # Track statistics
    stats = {
        'processed': 0,
        'skipped': 0,
        'errors': 0
    }
    
    for item in items:
        try:
            # Extract the type from the primary key
            pk = item.get('PK', '')
            if not pk:
                logger.warning(f"Skipping item with empty PK: {item}")
                stats['skipped'] += 1
                continue
                
            item_type = pk.split('#')[0]
            
            # Skip if type is not recognized
            if item_type not in ['CLUBE', 'CAPITULO', 'MEMBRO']:
                logger.warning(f"Skipping item with unknown type {item_type}: {item}")
                stats['skipped'] += 1
                continue
            
            # Log the full item for debugging
            logger.debug(f"Processing item: {item}")
            
            # Validate required fields based on type
            if item_type == 'CLUBE':
                nome_clube = item.get('NomeClube')
                if not nome_clube or nome_clube.strip() == '':
                    logger.warning(f"Skipping club with empty name. PK: {pk}, Full item: {item}")
                    stats['skipped'] += 1
                    continue
                    
                target_table = 'Clubes'
                new_item = {
                    'PK': pk,
                    'SK': item.get('SK', ''),
                    'NomeClube': nome_clube.strip(),
                    'Descricao': item.get('Descricao', ''),
                    'CriadoEm': item.get('CriadoEm', ''),
                    'AtualizadoEm': item.get('AtualizadoEm', '')
                }
                
                # Validate the new item before writing
                if not new_item['NomeClube'] or new_item['NomeClube'].strip() == '':
                    logger.warning(f"Skipping club with empty name after processing. PK: {pk}")
                    stats['skipped'] += 1
                    continue
                    
            elif item_type == 'CAPITULO':
                nome_capitulo = item.get('NomeCapitulo')
                if not nome_capitulo or nome_capitulo.strip() == '':
                    logger.warning(f"Skipping chapter with empty name. PK: {pk}, Full item: {item}")
                    stats['skipped'] += 1
                    continue
                    
                target_table = 'Capitulos'
                new_item = {
                    'PK': pk,
                    'SK': item.get('SK', ''),
                    'NomeCapitulo': nome_capitulo.strip(),
                    'Descricao': item.get('Descricao', ''),
                    'Fase': item.get('Fase', ''),
                    'CriadoEm': item.get('CriadoEm', ''),
                    'AtualizadoEm': item.get('AtualizadoEm', '')
                }
                
                # Validate the new item before writing
                if not new_item['NomeCapitulo'] or new_item['NomeCapitulo'].strip() == '':
                    logger.warning(f"Skipping chapter with empty name after processing. PK: {pk}")
                    stats['skipped'] += 1
                    continue
                    
            elif item_type == 'MEMBRO':
                nome_membro = item.get('NomeMembro')
                if not nome_membro or nome_membro.strip() == '':
                    logger.warning(f"Skipping member with empty name. PK: {pk}, Full item: {item}")
                    stats['skipped'] += 1
                    continue
                    
                target_table = 'Membros'
                new_item = {
                    'PK': pk,
                    'SK': item.get('SK', ''),
                    'NomeMembro': nome_membro.strip(),
                    'Cargo': item.get('Cargo', ''),
                    'CriadoEm': item.get('CriadoEm', ''),
                    'AtualizadoEm': item.get('AtualizadoEm', '')
                }
                
                # Validate the new item before writing
                if not new_item['NomeMembro'] or new_item['NomeMembro'].strip() == '':
                    logger.warning(f"Skipping member with empty name after processing. PK: {pk}")
                    stats['skipped'] += 1
                    continue
            
            # Log the new item before writing
            logger.debug(f"Writing to {target_table}: {new_item}")
            
            # Write to DynamoDB
            dynamodb.put_item(
                TableName=target_table,
                Item=new_item
            )
            stats['processed'] += 1
            
        except Exception as e:
            logger.error(f"Error distributing item {item.get('PK', 'UNKNOWN')}: {str(e)}")
            logger.error(f"Full item data: {item}")
            stats['errors'] += 1
    
    logger.info(f"Distribution complete. Processed: {stats['processed']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}") 
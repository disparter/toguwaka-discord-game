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
            
            # Validate required fields based on type
            if item_type == 'CLUBE':
                if not item.get('NomeClube'):
                    logger.warning(f"Skipping club with empty name: {item}")
                    stats['skipped'] += 1
                    continue
                target_table = 'Clubes'
                new_item = {
                    'PK': item['PK'],
                    'SK': item['SK'],
                    'NomeClube': item['NomeClube'],
                    'Descricao': item.get('Descricao', ''),
                    'CriadoEm': item.get('CriadoEm', ''),
                    'AtualizadoEm': item.get('AtualizadoEm', '')
                }
            elif item_type == 'CAPITULO':
                if not item.get('NomeCapitulo'):
                    logger.warning(f"Skipping chapter with empty name: {item}")
                    stats['skipped'] += 1
                    continue
                target_table = 'Capitulos'
                new_item = {
                    'PK': item['PK'],
                    'SK': item['SK'],
                    'NomeCapitulo': item['NomeCapitulo'],
                    'Descricao': item.get('Descricao', ''),
                    'Fase': item.get('Fase', ''),
                    'CriadoEm': item.get('CriadoEm', ''),
                    'AtualizadoEm': item.get('AtualizadoEm', '')
                }
            elif item_type == 'MEMBRO':
                if not item.get('NomeMembro'):
                    logger.warning(f"Skipping member with empty name: {item}")
                    stats['skipped'] += 1
                    continue
                target_table = 'Membros'
                new_item = {
                    'PK': item['PK'],
                    'SK': item['SK'],
                    'NomeMembro': item['NomeMembro'],
                    'Cargo': item.get('Cargo', ''),
                    'CriadoEm': item.get('CriadoEm', ''),
                    'AtualizadoEm': item.get('AtualizadoEm', '')
                }
            
            # Write to DynamoDB
            dynamodb.put_item(
                TableName=target_table,
                Item=new_item
            )
            stats['processed'] += 1
            
        except Exception as e:
            logger.error(f"Error distributing item {item.get('PK', 'UNKNOWN')}: {str(e)}")
            stats['errors'] += 1
    
    logger.info(f"Distribution complete. Processed: {stats['processed']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}") 
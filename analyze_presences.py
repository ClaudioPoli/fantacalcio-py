import pandas as pd

# Carica entrambi i file per verificare l'impatto migliorato delle presenze
df_fpedia = pd.read_excel('data/output/fpedia_analysis.xlsx')
df_fstats = pd.read_excel('data/output/FSTATS_analysis.xlsx')

print('=== ANALISI ALGORITMO MIGLIORATO: PRESENZE + AFFIDABILITÀ ===\n')

print('🔴 FPEDIA - Centrocampisti: Confronto FM simile ma presenze diverse:')
cen_fpedia = df_fpedia[df_fpedia['Ruolo'] == 'CEN'].copy()
cen_good = cen_fpedia[cen_fpedia['Fantamedia anno 2024-2025'] > 5].sort_values('Fantamedia anno 2024-2025')

print('Nome                     | FM 2024-25 | Presenze | Prezzo | Affidabilità Stimata')
print('-' * 80)
for _, row in cen_good.head(10).iterrows():
    fm = row['Fantamedia anno 2024-2025']
    presenze = row['Presenze campionato corrente']
    prezzo = row['Prezzo Massimo Consigliato']
    
    # Calcola affidabilità come nell'algoritmo
    if presenze >= 25:
        affidabilita = 100
        tipo = "Titolare fisso"
    elif presenze >= 15:
        affidabilita = int(70 + 30 * (presenze - 15) / 10)
        tipo = "Titolare"
    elif presenze >= 5:
        affidabilita = int(30 + 40 * (presenze - 5) / 10)
        tipo = "Riserva usata"
    elif presenze > 0:
        affidabilita = int(10 + 20 * presenze / 5)
        tipo = "Riserva"
    else:
        affidabilita = 5
        tipo = "Mai giocato"
    
    print(f'{row["Nome"]:24} | {fm:7.2f} | {presenze:8.0f} | {prezzo:6d} | {affidabilita:3d}% ({tipo})')

print('\n🔵 FSTATS - Attaccanti: Confronto FM simile ma presenze diverse:')
att_fstats = df_fstats[df_fstats['Ruolo'] == 'A'].copy()
att_good = att_fstats[att_fstats['fanta_avg'] > 5].sort_values('fanta_avg')

print('Nome                     | FM      | Presenze | Prezzo | Affidabilità Stimata')
print('-' * 75)
for _, row in att_good.head(10).iterrows():
    fm = row['fanta_avg']
    presenze = row['presences']
    prezzo = row['Prezzo Massimo Consigliato']
    
    if presenze >= 25:
        affidabilita = 100
        tipo = "Titolare fisso"
    elif presenze >= 15:
        affidabilita = int(70 + 30 * (presenze - 15) / 10)
        tipo = "Titolare"
    elif presenze >= 5:
        affidabilita = int(30 + 40 * (presenze - 5) / 10)
        tipo = "Riserva usata"
    elif presenze > 0:
        affidabilita = int(10 + 20 * presenze / 5)
        tipo = "Riserva"
    else:
        affidabilita = 5
        tipo = "Mai giocato"
    
    print(f'{row["Nome"]:24} | {fm:7.2f} | {presenze:8.0f} | {prezzo:6d} | {affidabilita:3d}% ({tipo})')

print('\n📊 VERIFICA: Esempi di GIUSTIZIA nell\'algoritmo migliorato:')

print('\n🎯 Caso 1 - Centrocampisti FPEDIA con FM simile (~5.5):')
caso1 = cen_fpedia[(cen_fpedia['Fantamedia anno 2024-2025'] >= 5.4) & (cen_fpedia['Fantamedia anno 2024-2025'] <= 5.7)]
caso1_sorted = caso1.sort_values('Presenze campionato corrente', ascending=False)
for _, row in caso1_sorted.head(5).iterrows():
    fm = row['Fantamedia anno 2024-2025']
    presenze = row['Presenze campionato corrente']
    prezzo = row['Prezzo Massimo Consigliato']
    print(f'   {row["Nome"]:20} | FM: {fm:.2f} | Presenze: {presenze:2.0f} | Prezzo: {prezzo:2d} | Ratio: {prezzo/(fm*10):.1f}')

print('\n🎯 Caso 2 - Attaccanti FSTATS con FM simile (~5.7):')
caso2 = att_fstats[(att_fstats['fanta_avg'] >= 5.6) & (att_fstats['fanta_avg'] <= 5.8)]
caso2_sorted = caso2.sort_values('presences', ascending=False)
for _, row in caso2_sorted.head(5).iterrows():
    fm = row['fanta_avg']
    presenze = row['presences']
    prezzo = row['Prezzo Massimo Consigliato']
    print(f'   {row["Nome"]:20} | FM: {fm:.2f} | Presenze: {presenze:2.0f} | Prezzo: {prezzo:2d} | Ratio: {prezzo/(fm*10):.1f}')

print('\n💡 MIGLIORAMENTI IMPLEMENTATI:')
print('')
print('✅ FATTORE DI AFFIDABILITÀ:')
print('   • Titolari fissi (≥25 presenze): 100% affidabilità → FM conta al massimo')
print('   • Titolari (15-24 presenze): 70-100% affidabilità → FM scala proporzionalmente')
print('   • Riserve usate (5-14 presenze): 30-70% affidabilità → FM molto ridotta')
print('   • Riserve rare (1-4 presenze): 10-30% affidabilità → FM quasi ignorata')
print('   • Mai giocato (0 presenze): 5% affidabilità → FM praticamente zero')
print('')
print('✅ PESO DELLE PRESENZE:')
print('   • FPEDIA: Presenze ora hanno peso 20% (era 15%)')
print('   • FSTATS: Presenze + Titolarità ora hanno peso 22% (era 15%)')
print('')
print('✅ BONUS TITOLARITÀ:')
print('   • Titolarissimi (≥30 presenze): 100% bonus')
print('   • Titolari fissi (≥25 presenze): 90% bonus')
print('   • Panchinari (<5 presenze): Solo 5-15% bonus')
print('')
print('✅ STATISTICHE PER PRESENZA:')
print('   • xG/Goals/Assists ora sono calcolati PER PARTITA')
print('   • Un attaccante con 10 gol in 30 partite > uno con 10 gol in 10 partite')
print('')
print('🎯 RISULTATO: Chi gioca di più e con continuità ora viene valutato MOLTO meglio!')

# 🗜️ Compactação de Histórico

À medida que o roleplay prossegue, o histórico de turnos cresce e pode consumir muitos tokens de contexto da LLM.

## Como funciona
1. A compactação preserva os **últimos N turnos** literalmente (definidos nas configurações).
2. Condensa toda a prosa narrativa antiga em um **resumo da história pública** e em **notas de personagens isoladas**.
3. Realiza um backup da sessão antes de compactar, permitindo desfazer a compactação se nenhum turno novo tiver sido jogado.

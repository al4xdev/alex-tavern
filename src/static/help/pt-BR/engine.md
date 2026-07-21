# 🎬 Roteiro & Motor do Backend

O Alex Tavern opera através de uma arquitetura determinística orientada a estado, onde a agência humana é preservada e o mundo é governado por papéis bem definidos.

---

### 1. Arquitetura do Runner e Estado Canônico

- **Estado Único Persistido:** Todas as falas, ações, pensamentos, locais e estados emocionais vivem num arquivo JSON por sessão (`state.json`).
- **Locks Transacionais:** Cada turno, desfazer (undo) ou compactação adquire um lock exclusivo por sessão. Nenhuma mutação ocorre fora dessa trava de segurança.
- **Trava de Agência Humana:** O humano controla exclusivamente o seu personagem. As IA de Personagem jamais decidem as falas, ações físicas ou pensamentos do seu personagem.

---

### 2. O Roteiro Privado (*Screenplay*), Atos e Beats

Quando a opção **Roteiro da história** está ativada:

- **Diretor Omnisciente:** O Diretor compila um plano narrativo privado que os personagens não veem.
- **Atos e Beats:** A história é dividida em **Atos** (arcos maiores) e **Beats** (objetivos dramáticos imediatos de cena).
- **Atores Esperados (*Expected Actors*):** Cada beat define a intenção dramática e quais personagens são chamados a interagir naquela etapa.

---

### 3. Reescrita e Replanejamento (*Beat Replans*)

O Alex Tavern não é um livro engessado. Se a história tomar um rumo inesperado (por conta de uma ação humana ou reação orgânica dos personagens):

- O Diretor detecta a divergência e executa um **Replan** (reescrita adaptativa do beat ou ato).
- O roteiro se adapta ao que acabou de acontecer na cena, reajustando os objetivos futuros sem quebrar a coerência.

---

### 4. Alinhamento Dramático de Personagens (Toggle 2)

- **Lógica de Atuação:** Quando o alinhamento de personagens está ativado, agentes em *Expected Actors* recebem um **impulso dramático transiente** (como *audacioso*, *urgente* ou *cauteloso*).
- **Sem Vazamentos (*Leak-Safe*):** O personagem recebe apenas um sentimento genérico (enum), nunca os fatos privados do roteiro ou spoilers do futuro. Ele escolhe colaborar com a história mantendo sua própria voz e personalidade.

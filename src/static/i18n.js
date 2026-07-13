const STORAGE_KEY = 'rpt_interface_locale_v1';
const DEFAULT_LOCALE = 'en';
const LLM_LANGUAGES = Object.freeze({ en: 'English', 'pt-BR': 'Brazilian Portuguese' });

const en = {
    'app.description': 'Multi-agent roleplay: Narrator + characters, configurable in the UI.',
    'common.close': 'Close',
    'common.remove': 'Remove',
    'common.delete': 'Delete',
    'common.loading': 'LOADING',
    'common.unavailable': 'UNAVAILABLE',
    'preferences.title': '🌐 Application preferences',
    'preferences.hint': 'Changes only application controls and messages, not story language.',
    'preferences.language': 'Interface language',
    'setup.title': 'Configure adventure',
    'setup.subtitle': 'Build the scene, characters, and tone of the world',
    'engine.title': '⚡ AI engine',
    'engine.hint': 'Choose where the story is processed. Saved on the server, never in the browser.',
    'engine.providerAria': 'Artificial intelligence provider',
    'engine.compactTurns': 'Recent turns kept after compaction',
    'engine.save': 'Save engine',
    'engine.statusActive': '{kind} ACTIVE',
    'engine.loadError': 'Could not load the engine: {error}',
    'engine.saveError': 'Could not save: {error}',
    'engine.updated': 'AI engine updated',
    'engine.languageSyncError': 'Interface changed, but the model language could not be saved: {error}',
    'engine.missingAdapter': 'Frontend adapter missing for {name}',
    'engine.adapterMismatch': 'Adapter mismatch: backend={backend} frontend={frontend}',
    'provider.localDescription': 'Local · your machine or network',
    'provider.cloudDescription': 'Cloud · no reasoning',
    'provider.reasoningDisabled': 'Reasoning disabled. The backend sends thinking.type = disabled on every request.',
    'provider.apiBase': 'API base',
    'provider.model': 'Model',
    'provider.context': 'Context',
    'provider.narrator': 'Narrator',
    'provider.character': 'Character',
    'provider.summary': 'Summary',
    'provider.timeout': 'Timeout (s)',
    'provider.apiKey': 'API key',
    'provider.llamaHint': 'Include /v1 for the llama.cpp OpenAI endpoint.',
    'provider.emptyModel': 'Empty uses the loaded model',
    'provider.newKey': 'Paste a new key or leave blank to keep it',
    'provider.keyConfigured': 'Key configured on the server. Leave blank to keep it.',
    'provider.keyMissing': 'No key configured. It will be saved only on the server.',
    'help.title': 'Help & Guides',
    'help.menu.roleplay': '🎭 Roleplay & Rules',
    'help.menu.compaction': '🗜️ History Compaction',
    'help.menu.settings': '⚡ AI Engine & Settings',
    'help.menu.commands': '💬 Shortcuts & Features',
    'help.menu.gestures': '📱 Mobile Gestures',
    'help.menu.actions': '⚙️ Action Menu',
    'help.back': '← Back',
    'help.warning.roleplay': '💡 Tip: The Narrator orchestrates the physical world, while Characters express speech and thoughts. Click here to read the roleplay guide.',
    'help.warning.compaction': '💡 Tip: If your session becomes slow or runs out of context, you can compact old turns using the 🗜️ button. Click here to learn more.',
    'help.warning.settings': '💡 Tip: Adjust context size and max tokens in settings to optimize performance. Click here to read the guide.',
    'help.warning.gestures': '💡 Tip: Swipe up or down on the scene panel to expand or collapse it on mobile. Click here to read the mobile gestures guide.',
    'help.warning.actions': '💡 Tip: Hover or long-press the Send button to reveal advanced controls like skip and suggest. Click here to read the action menu guide.',
    'presets.title': '💾 Presets',
    'presets.savedAria': 'Saved preset',
    'presets.load': 'Load',
    'presets.delete': 'Delete preset',
    'presets.namePlaceholder': 'New preset name (e.g. Pirate campaign)',
    'presets.saveCurrent': 'Save current',
    'presets.builtinSuffix': 'default',
    'presets.defaultLoaded': 'Default preset “{name}” loaded',
    'presets.loaded': 'Preset “{name}” loaded',
    'presets.saved': 'Preset “{name}” saved',
    'presets.deleted': 'Preset “{name}” deleted',
    'presets.defaultLoadError': 'Could not load the default preset: {error}',
    'presets.refreshError': 'Could not refresh presets: {error}',
    'presets.serverLoadError': 'Could not load the server preset: {error}',
    'presets.nameRequired': 'Give the preset a name before saving.',
    'presets.saveError': 'Could not save preset: {error}',
    'presets.deleteError': 'Could not delete preset: {error}',
    'setup.directives': 'Narrator directives',
    'setup.directivesHint': 'World, tone, and extra rules the Narrator must always respect.',
    'setup.directivesPlaceholder': 'E.g. Dark fantasy. Magic is rare and feared. Keep the tone tense.',
    'setup.scene': '🗺️ Scene',
    'setup.location': 'Location',
    'setup.locationPlaceholder': 'Old Mork’s Tavern',
    'setup.time': 'Time of day',
    'setup.timePlaceholder': 'night',
    'setup.physicalFacts': 'Physical facts',
    'setup.physicalFactsHint': 'Environment details (key / value).',
    'setup.addFact': '+ Fact',
    'setup.keyPlaceholder': 'key',
    'setup.valuePlaceholder': 'value',
    'setup.characters': '👥 Characters',
    'setup.addCharacter': '+ Character',
    'setup.controlled': 'Who do you control?',
    'setup.start': 'Start adventure →',
    'character.namePlaceholder': 'Character name',
    'character.personality': 'Personality',
    'character.personalityPlaceholder': 'Description of the character’s personality',
    'character.mood': 'Current mood',
    'character.moodPlaceholder': 'cautious',
    'character.outfit': 'Outfit',
    'character.outfitPlaceholder': 'Leather armor',
    'character.physical': 'Physical appearance',
    'character.physicalPlaceholder': 'Tall, scar on the chin',
    'character.knowledge': 'Knowledge',
    'character.knowledgePlaceholder': 'A fact the character knows',
    'character.addKnowledge': '+ Known fact',
    'validation.addCharacter': 'Add at least one character.',
    'validation.characterName': 'Character {id} needs a name.',
    'validation.personality': 'Character {name} needs a personality.',
    'validation.location': 'The scene needs a location.',
    'validation.controlled': 'Choose which character you control.',
    'sessions.title': 'Sessions',
    'sessions.subtitle': 'Select, fork, or delete your adventures',
    'sessions.close': 'Close sessions',
    'sessions.empty': 'No sessions yet.',
    'sessions.emptyCreate': 'No sessions yet. Create one!',
    'sessions.new': '➕ New session',
    'sessions.manage': 'Manage sessions',
    'sessions.fork': 'Fork (copy)',
    'sessions.turns': '{count} turns',
    'sessions.now': 'now',
    'sessions.minutesAgo': '{count}m ago',
    'sessions.hoursAgo': '{count}h ago',
    'sessions.daysAgo': '{count}d ago',
    'sessions.listError': 'Could not list sessions: {error}',
    'sessions.forked': 'Fork created: {id}',
    'sessions.forkError': 'Could not fork: {error}',
    'sessions.deleteConfirm': 'Delete session {id}?',
    'sessions.deleted': 'Session deleted',
    'sessions.deleteError': 'Could not delete: {error}',
    'sessions.loaded': 'Session {id} loaded',
    'sessions.loadError': 'Could not load session: {error}',
    'header.install': '⬇ Install',
    'header.debugMode': 'Debug mode',
    'header.settings': 'Configure',
    'empty.prompt': 'Configure your adventure to begin',
    'empty.open': 'Open configuration',
    'debug.close': 'Close debug',
    'debug.refresh': '🔄 Log',
    'debug.preview': 'Prompt preview',
    'debug.instructions': 'Click “🔄 Log” to see this session’s raw LLM call history, or “Prompt preview” to build it without calling the LLM.',
    'debug.shortInstructions': 'Click “🔄 Log” or “Prompt preview”.',
    'debug.noCalls': 'No LLM calls recorded in this session yet.',
    'debug.logTitle': 'Turn {turn} · {agent}{error}{metrics}',
    'debug.logErrorSuffix': ' · ERROR',
    'debug.logMetrics': ' · attempt {attempt} · {duration} ms',
    'debug.copy': 'Copy JSON',
    'debug.copied': 'Copied!',
    'debug.copyError': 'Could not copy',
    'debug.previewNarrator': 'Preview — Narrator',
    'debug.previewReady': 'Narrator prompt built (without calling the LLM)',
    'debug.startFirst': 'Start a session first',
    'debug.logError': 'Could not load debug log: {error}',
    'debug.previewError': 'Could not build preview: {error}',
    'loading.processing': 'Processing...',
    'loading.stop': 'Stop',
    'loading.stopAria': 'Stop processing',
    'input.expand': '💬 Write message...',
    'input.speech': '💬 Speech...',
    'input.thought': '💭 Private thought...',
    'input.action': '🎬 Action...',
    'input.actionAs': '🎬 Action (you are {name})',
    'input.send': 'Send',
    'input.you': 'You',
    'input.narrator': 'Narrator',
    'action.forceTitle': 'Force who acts next',
    'action.forceAria': 'Force speaker',
    'action.automatic': '🎲 Automatic',
    'action.suggestTitle': 'Move suggestion',
    'action.suggestAria': 'Suggest a move',
    'action.hintTitle': 'Narrator event hint',
    'action.hintAria': 'Suggest an event for the Narrator',
    'action.compactTitle': 'Compact session (summarize old turns)',
    'action.compactAria': 'Compact session history',
    'action.restoreTitle': 'Undo last compaction (only when safe)',
    'action.restoreAria': 'Undo last compaction',
    'action.undoTitle': 'Undo turn',
    'action.undoAria': 'Undo last turn',
    'action.retryTitle': 'Try again',
    'action.retryAria': 'Resend turn',
    'action.skipTitle': 'Skip turn',
    'action.skipAria': 'Skip player turn',
    'action.inputRequired': 'Write speech, a thought, or an action',
    'turn.noneToUndo': 'Nothing to undo',
    'turn.undone': 'Turn undone',
    'turn.undoError': 'Could not undo: {error}',
    'turn.startError': 'Could not start session: {error}',
    'turn.started': 'Adventure started as {name}',
    'turn.failed': 'Turn failed: {error}. Is the LLM running?',
    'turn.stopped': 'Generation stopped',
    'suggestion.fallback': 'Option {number}',
    'suggestion.ready': 'Suggestions ready — choose one',
    'suggestion.error': 'Could not suggest a move: {error}',
    'compaction.done': 'Session compacted — {evicted} records summarized, {kept} kept',
    'compaction.none': 'Nothing to compact yet',
    'compaction.error': 'Could not compact session: {error}',
    'compaction.restoreConfirm': 'Undo the last compaction? This only works if no new turns have been played since.',
    'compaction.restored': 'Compaction undone — history restored ({count} records)',
    'compaction.restoreUnavailable': 'Could not undo compaction',
    'compaction.restoreError': 'Could not undo compaction: {error}',
    'pwa.installed': 'App installed 🎉',
};

const ptBR = {
    'app.description': 'Roleplay multi-agente: Narrador + personagens, configurável pela UI.',
    'common.close': 'Fechar', 'common.remove': 'Remover', 'common.delete': 'Apagar',
    'common.loading': 'CARREGANDO', 'common.unavailable': 'INDISPONÍVEL',
    'preferences.title': '🌐 Preferências do aplicativo',
    'preferences.hint': 'Altera apenas os controles e mensagens do aplicativo, não o idioma da história.',
    'preferences.language': 'Idioma da interface',
    'setup.title': 'Configurar aventura', 'setup.subtitle': 'Monte a cena, os personagens e o tom do mundo',
    'engine.title': '⚡ Motor de IA',
    'engine.hint': 'Escolha onde a história é processada. Salvo no servidor, nunca no navegador.',
    'engine.providerAria': 'Provedor de inteligência artificial',
    'engine.compactTurns': 'Turnos recentes após compactar',
    'engine.save': 'Salvar motor', 'engine.statusActive': '{kind} ATIVO',
    'engine.loadError': 'Não foi possível carregar o motor: {error}',
    'engine.saveError': 'Não foi possível salvar: {error}', 'engine.updated': 'Motor de IA atualizado',
    'engine.languageSyncError': 'A interface mudou, mas não foi possível salvar o idioma do modelo: {error}',
    'engine.missingAdapter': 'Adapter de frontend ausente para {name}',
    'engine.adapterMismatch': 'Adapters divergentes: backend={backend} frontend={frontend}',
    'provider.localDescription': 'Local · sua máquina ou rede', 'provider.cloudDescription': 'Cloud · sem reasoning',
    'provider.reasoningDisabled': 'Reasoning desativado. O backend envia thinking.type = disabled em toda chamada.',
    'provider.apiBase': 'Base da API', 'provider.model': 'Modelo', 'provider.context': 'Contexto',
    'provider.narrator': 'Narrador', 'provider.character': 'Personagem', 'provider.summary': 'Resumo',
    'provider.apiKey': 'Chave da API', 'provider.llamaHint': 'Inclua /v1 para o endpoint OpenAI do llama.cpp.',
    'provider.emptyModel': 'Vazio usa o modelo carregado',
    'provider.newKey': 'Cole uma nova chave ou deixe em branco para manter',
    'provider.keyConfigured': 'Chave configurada no servidor. Deixe em branco para mantê-la.',
    'provider.keyMissing': 'Nenhuma chave configurada. Ela será salva somente no servidor.',
    'help.title': 'Ajuda & Guias',
    'help.menu.roleplay': '🎭 Roleplay & Regras',
    'help.menu.compaction': '🗜️ Compactação de Histórico',
    'help.menu.settings': '⚡ Motor de IA & Configurações',
    'help.menu.commands': '💬 Atalhos & Recursos',
    'help.menu.gestures': '📱 Gestos no Celular',
    'help.menu.actions': '⚙️ Menu de Ações',
    'help.back': '← Voltar',
    'help.warning.roleplay': '💡 Dica: O Narrador orquestra o mundo físico, enquanto os Personagens expressam fala e pensamento. Clique aqui para ler o guia de roleplay.',
    'help.warning.compaction': '💡 Dica: Se a sessão ficar lenta ou sem contexto, você pode compactar os turnos antigos usando o botão 🗜️. Clique aqui para saber mais.',
    'help.warning.settings': '💡 Dica: Ajuste o tamanho do contexto e o limite de tokens nas configurações para otimizar o desempenho. Clique aqui para ler o guia.',
    'help.warning.gestures': '💡 Dica: Deslize para cima ou para baixo no painel da cena para expandi-lo ou recolhê-lo no celular. Clique aqui para ler o guia de gestos.',
    'help.warning.actions': '💡 Dica: Passe o mouse ou mantenha pressionado o botão Enviar para revelar opções avançadas como pular e sugestões. Clique aqui para o guia do menu.',
    'presets.savedAria': 'Preset salvo', 'presets.load': 'Carregar', 'presets.delete': 'Apagar preset',
    'presets.namePlaceholder': 'Nome do novo preset (ex: Campanha pirata)', 'presets.saveCurrent': 'Salvar atual',
    'presets.builtinSuffix': 'padrão', 'presets.defaultLoaded': 'Preset padrão “{name}” carregado',
    'presets.loaded': 'Preset “{name}” carregado', 'presets.saved': 'Preset “{name}” salvo',
    'presets.deleted': 'Preset “{name}” apagado',
    'presets.defaultLoadError': 'Não foi possível carregar o preset padrão: {error}',
    'presets.refreshError': 'Erro ao atualizar presets: {error}',
    'presets.serverLoadError': 'Erro ao carregar preset do servidor: {error}',
    'presets.nameRequired': 'Dê um nome ao preset antes de salvar.',
    'presets.saveError': 'Erro ao salvar preset: {error}', 'presets.deleteError': 'Erro ao apagar preset: {error}',
    'setup.directives': 'Diretrizes do Narrador',
    'setup.directivesHint': 'Mundo, tom, regras extras que o Narrador sempre respeita.',
    'setup.directivesPlaceholder': 'Ex: Fantasia sombria. Magia é rara e temida. Mantenha o tom tenso.',
    'setup.scene': '🗺️ Cena', 'setup.location': 'Local', 'setup.locationPlaceholder': 'Taverna do Velho Mork',
    'setup.time': 'Momento do dia', 'setup.timePlaceholder': 'noite', 'setup.physicalFacts': 'Fatos físicos',
    'setup.physicalFactsHint': 'Detalhes do ambiente (chave / valor).', 'setup.addFact': '+ Fato',
    'setup.keyPlaceholder': 'chave', 'setup.valuePlaceholder': 'valor', 'setup.characters': '👥 Personagens',
    'setup.addCharacter': '+ Personagem', 'setup.controlled': 'Quem você controla?',
    'setup.start': 'Começar aventura →', 'character.namePlaceholder': 'Nome do personagem',
    'character.personality': 'Personalidade',
    'character.personalityPlaceholder': 'Descrição da personalidade do personagem',
    'character.mood': 'Humor atual', 'character.moodPlaceholder': 'cauteloso', 'character.outfit': 'Roupa',
    'character.outfitPlaceholder': 'Armadura de couro', 'character.physical': 'Aparência física',
    'character.physicalPlaceholder': 'Alto, cicatriz no queixo', 'character.knowledge': 'Conhecimento',
    'character.knowledgePlaceholder': 'Um fato que o personagem conhece',
    'character.addKnowledge': '+ Fato conhecido', 'validation.addCharacter': 'Adicione ao menos um personagem.',
    'validation.characterName': 'Personagem {id} precisa de um nome.',
    'validation.personality': 'Personagem {name} precisa de uma personalidade.',
    'validation.location': 'A cena precisa de um local.',
    'validation.controlled': 'Escolha qual personagem você controla.',
    'sessions.title': 'Sessões', 'sessions.subtitle': 'Selecione, fork ou apague suas aventuras',
    'sessions.close': 'Fechar sessões', 'sessions.empty': 'Nenhuma sessão ainda.',
    'sessions.emptyCreate': 'Nenhuma sessão ainda. Crie uma nova!', 'sessions.new': '➕ Nova sessão',
    'sessions.manage': 'Gerenciar sessões', 'sessions.fork': 'Fork (copiar)',
    'sessions.turns': '{count} turnos', 'sessions.now': 'agora', 'sessions.minutesAgo': 'há {count}m',
    'sessions.hoursAgo': 'há {count}h', 'sessions.daysAgo': 'há {count}d',
    'sessions.listError': 'Erro ao listar sessões: {error}', 'sessions.forked': 'Fork criado: {id}',
    'sessions.forkError': 'Erro no fork: {error}', 'sessions.deleteConfirm': 'Apagar sessão {id}?',
    'sessions.deleted': 'Sessão apagada', 'sessions.deleteError': 'Erro ao apagar: {error}',
    'sessions.loaded': 'Sessão {id} carregada', 'sessions.loadError': 'Erro ao carregar sessão: {error}',
    'header.install': '⬇ Instalar', 'header.debugMode': 'Modo debug', 'header.settings': 'Configurar',
    'empty.prompt': 'Configure sua aventura para começar', 'empty.open': 'Abrir configuração',
    'debug.close': 'Fechar debug', 'debug.preview': 'Preview do prompt',
    'debug.instructions': 'Clique em “🔄 Log” pra ver o histórico bruto de chamadas ao LLM desta sessão, ou “Preview do prompt” pra montar sem chamar o LLM.',
    'debug.shortInstructions': 'Clique em “🔄 Log” ou “Preview do prompt”.',
    'debug.noCalls': 'Nenhuma chamada LLM registrada ainda nesta sessão.', 'debug.copy': 'Copiar JSON',
    'debug.logTitle': 'Turno {turn} · {agent}{error}{metrics}',
    'debug.logErrorSuffix': ' · ERRO', 'debug.logMetrics': ' · tentativa {attempt} · {duration} ms',
    'debug.copied': 'Copiado!', 'debug.copyError': 'Não foi possível copiar',
    'debug.previewNarrator': 'Preview — Narrador', 'debug.startFirst': 'Inicie uma sessão primeiro',
    'debug.previewReady': 'Prompt do Narrador montado (sem chamar o LLM)',
    'debug.logError': 'Erro ao carregar log: {error}', 'debug.previewError': 'Erro no preview: {error}',
    'loading.processing': 'Processando...', 'loading.stop': 'Parar',
    'loading.stopAria': 'Parar processamento', 'input.expand': '💬 Escrever mensagem...', 'input.speech': '💬 Fala...',
    'input.thought': '💭 Pensamento privado...', 'input.action': '🎬 Ação...',
    'input.actionAs': '🎬 Ação (você é {name})', 'input.send': 'Enviar', 'input.you': 'Você',
    'input.narrator': 'Narrador', 'action.forceTitle': 'Forçar quem age a seguir',
    'action.forceAria': 'Forçar falante', 'action.automatic': '🎲 Automático',
    'action.suggestTitle': 'Sugestão de jogada', 'action.suggestAria': 'Sugerir jogada',
    'action.hintTitle': 'Sugestão de evento', 'action.hintAria': 'Sugerir evento para o Narrador',
    'action.compactTitle': 'Compactar sessão (resume turnos antigos)',
    'action.compactAria': 'Compactar histórico da sessão',
    'action.restoreTitle': 'Desfazer última compactação (só se seguro)',
    'action.restoreAria': 'Desfazer última compactação', 'action.undoTitle': 'Desfazer turno',
    'action.undoAria': 'Desfazer último turno', 'action.retryTitle': 'Tentar de novo',
    'action.retryAria': 'Reenviar turno', 'action.skipTitle': 'Pular turno',
    'action.skipAria': 'Pular turno do jogador', 'action.inputRequired': 'Escreva uma fala, pensamento ou ação',
    'turn.noneToUndo': 'Nada a desfazer', 'turn.undone': 'Turno desfeito',
    'turn.undoError': 'Erro ao desfazer: {error}', 'turn.startError': 'Erro ao iniciar sessão: {error}',
    'turn.started': 'Aventura iniciada como {name}',
    'turn.failed': 'Falha no turno: {error}. O LLM está rodando?', 'turn.stopped': 'Geração interrompida',
    'suggestion.fallback': 'Opção {number}',
    'suggestion.ready': 'Sugestões prontas — escolha uma',
    'suggestion.error': 'Erro ao sugerir jogada: {error}',
    'compaction.done': 'Sessão compactada — {evicted} registros resumidos, {kept} mantidos',
    'compaction.none': 'Nada para compactar ainda',
    'compaction.error': 'Erro ao compactar sessão: {error}',
    'compaction.restoreConfirm': 'Desfazer a última compactação? Isso só funciona se nenhum turno novo foi jogado desde então.',
    'compaction.restored': 'Compactação desfeita — histórico restaurado ({count} registros)',
    'compaction.restoreUnavailable': 'Não foi possível desfazer a compactação',
    'compaction.restoreError': 'Erro ao desfazer compactação: {error}', 'pwa.installed': 'App instalado 🎉',
};

export const catalogs = Object.freeze({ en: Object.freeze(en), 'pt-BR': Object.freeze(ptBR) });
const SUPPORTED_LOCALES = Object.freeze(Object.keys(catalogs));

export function normalizeLocale(locale) {
    if (typeof locale !== 'string') return null;
    const normalized = locale.trim().toLowerCase();
    const exact = SUPPORTED_LOCALES.find((candidate) => candidate.toLowerCase() === normalized);
    if (exact) return exact;
    const base = normalized.split('-')[0];
    return SUPPORTED_LOCALES.find((candidate) => candidate.toLowerCase().split('-')[0] === base) || null;
}

export function detectLocale(languages = []) {
    for (const language of languages || []) {
        const supported = normalizeLocale(language);
        if (supported) return supported;
    }
    return DEFAULT_LOCALE;
}

function readSavedLocale() {
    try { return normalizeLocale(globalThis.localStorage?.getItem(STORAGE_KEY)); }
    catch { return null; }
}

function browserLanguages() {
    const values = globalThis.navigator?.languages;
    if (Array.isArray(values) && values.length) return values;
    return globalThis.navigator?.language ? [globalThis.navigator.language] : [];
}

let currentLocale = readSavedLocale() || detectLocale(browserLanguages());
const listeners = new Set();

export function getLocale() { return currentLocale; }

export function getLlmLanguage(locale = currentLocale) {
    return LLM_LANGUAGES[normalizeLocale(locale) || DEFAULT_LOCALE];
}

export function t(key, params = {}, locale = currentLocale) {
    const selected = catalogs[normalizeLocale(locale) || DEFAULT_LOCALE] || catalogs[DEFAULT_LOCALE];
    const template = selected[key] ?? catalogs[DEFAULT_LOCALE][key] ?? '';
    return template.replace(/\{(\w+)\}/g, (_, name) => String(params[name] ?? ''));
}

function readParams(element) {
    try { return JSON.parse(element.dataset.i18nParams || '{}'); }
    catch { return {}; }
}

export function translateElement(element) {
    const params = readParams(element);
    if (element.dataset.i18n) element.textContent = t(element.dataset.i18n, params);
    if (element.dataset.i18nPlaceholder) element.placeholder = t(element.dataset.i18nPlaceholder, params);
    if (element.dataset.i18nTitle) element.title = t(element.dataset.i18nTitle, params);
    if (element.dataset.i18nAriaLabel) element.setAttribute('aria-label', t(element.dataset.i18nAriaLabel, params));
    if (element.dataset.i18nContent) element.setAttribute('content', t(element.dataset.i18nContent, params));
    return element;
}

export function bindTranslation(element, key, params = {}, attribute = 'text') {
    const suffixes = { text: 'i18n', placeholder: 'i18nPlaceholder', title: 'i18nTitle', ariaLabel: 'i18nAriaLabel' };
    element.dataset[suffixes[attribute] || 'i18n'] = key;
    element.dataset.i18nParams = JSON.stringify(params);
    return translateElement(element);
}

export function translateDocument(root = globalThis.document) {
    if (!root) return;
    const selector = '[data-i18n], [data-i18n-placeholder], [data-i18n-title], [data-i18n-aria-label], [data-i18n-content]';
    if (root.matches?.(selector)) translateElement(root);
    root.querySelectorAll?.(selector).forEach(translateElement);
    if (root.documentElement) root.documentElement.lang = currentLocale;
}

export function onLocaleChange(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
}

export function setLocale(locale, { persist = true } = {}) {
    const next = normalizeLocale(locale) || DEFAULT_LOCALE;
    currentLocale = next;
    if (persist) {
        try { globalThis.localStorage?.setItem(STORAGE_KEY, next); } catch { /* optional */ }
    }
    translateDocument();
    listeners.forEach((listener) => listener(next));
    return next;
}

export const i18nConfig = Object.freeze({ STORAGE_KEY, DEFAULT_LOCALE, SUPPORTED_LOCALES });

translateDocument();

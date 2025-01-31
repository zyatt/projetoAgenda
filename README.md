Aplicativo de Agenda Tkinter

- Visão Geral
• Este aplicativo Python, construído utilizando a biblioteca tkinter, funciona como uma agenda para gerenciar tarefas diárias. 
Ele possui uma interface de calendário, campos para entrada de dados, capacidade de exportar dados para PDF e funcionalidade de salvamento automático. 
Permite que os usuários insiram e gerenciem várias informações e as exportem para uso posterior.

- Funcionalidades
• Integração com Calendário: Permite que os usuários selecionem uma data específica usando um calendário integrado.
• Entrada de Dados: Vários campos de entrada para tarefas como "Orçamentos Enviados", "Pedido", "Arquivos Produzidos", entre outros.
• Salvar Dados Automaticamente: Os dados são salvos automaticamente em um arquivo JSON e também é possível salvar manualmente usando um atalho de teclado.
• Exportar para PDF: Gera um PDF com o layout atual da tela.
• Exportar para PNG: Gera um PNG com o layout atual da tela.
• Manipulação de Imagens e Logo: Suporta exibição de imagens, como logotipos.
• Áreas de Entrada Personalizáveis: Campos de entrada dinâmicos com limites de caracteres ajustáveis e layouts configuráveis.

- Interagindo com o Aplicativo:
• Calendário: Clique no botão "Abrir Calendário" para abrir o calendário e selecionar uma data.
• Entrada de Dados: Preencha os diversos campos como "Orçamentos Enviados", "Pedido", entre outros. Cada seção possui várias linhas para entradas detalhadas.
• Exportar para PDF: Clique no botão "Exportar" para salvar a tela atual como um arquivo PDF.
• Salvar Dados: O aplicativo salva automaticamente os dados no arquivo dados.json, e você pode salvar manualmente usando o atalho de teclado Ctrl+S.
• Salvando Dados: O aplicativo salva os dados automaticamente a cada segundo e os armazena com base na data selecionada. Se não houver dados disponíveis para a data selecionada, os campos serão limpos.

- Exportação para PDF:
• Ao exportar para PDF, uma captura de tela da janela atual é feita e incluída no arquivo PDF.

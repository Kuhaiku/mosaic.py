const express = require('express');
const mysql = require('mysql2/promise');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

// Configuração do Banco de Dados (Idealmente, coloque isso num arquivo .env)
const dbConfig = {
    host: '136.248.87.149',
    port:   '3051',
    user: 'root',
    password: 'Raposo88125442@@',
    database: 'raposo_licencas'
};

// Endpoint Único de Validação
app.post('/api/validar-licenca', async (req, res) => {
    const { chave, hwid, produto_id } = req.body;

    if (!chave || !hwid || !produto_id) {
        return res.status(400).json({ error: "Faltam parâmetros na requisição." });
    }

    try {
        const connection = await mysql.createConnection(dbConfig);
        
        // Busca a licença atrelada ao produto específico
        const [rows] = await connection.execute(
            'SELECT * FROM licencas WHERE chave = ? AND produto_id = ?',
            [chave, produto_id]
        );

        if (rows.length === 0) {
            await connection.end();
            return res.status(404).json({ error: "Chave não encontrada para este produto." });
        }

        const licenca = rows[0];

        if (!licenca.ativa) {
            await connection.end();
            return res.status(403).json({ error: "Esta chave foi desativada." });
        }

        const hoje = new Date();
        const dataExp = new Date(licenca.data_expiracao);
        if (hoje > dataExp) {
            await connection.end();
            return res.status(403).json({ error: "Sua licença expirou." });
        }

        // Cenário 1: Primeira ativação (HWID está null no banco)
        if (!licenca.hwid) {
            await connection.execute(
                'UPDATE licencas SET hwid = ? WHERE id = ?',
                [hwid, licenca.id]
            );
            await connection.end();
            return res.status(200).json({ message: "Software ativado e vinculado a este computador!" });
        }

        // Cenário 2: Validação de rotina (Verifica se é o PC correto)
        if (licenca.hwid !== hwid) {
            await connection.end();
            return res.status(403).json({ error: "Esta licença pertence a outro computador." });
        }

        // Tudo certo
        await connection.end();
        return res.status(200).json({ message: "Licença validada com sucesso." });

    } catch (err) {
        console.error(err);
        return res.status(500).json({ error: "Erro interno no servidor de licenças." });
    }
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`API da Raposo.tech rodando na porta ${PORT}`);
});
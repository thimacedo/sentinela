
const text = `Claro, aqui está o resultado da sua query SQL no Supabase:

\`\`\`json
[{"id": 1, "total": 100}, {"id": 2, "total": 200}]
\`\`\`

Espero que isso ajude!`;

// O mesmo regex usado no Dashboard.jsx
const match = text.match(/\[[\s\S]*\]|\{[\s\S]*\}/);

if (match) {
    try {
        const json = JSON.parse(match[0]);
        console.log('✅ Parser OK!');
        console.log('Extraído:', JSON.stringify(json, null, 2));
    } catch (e) {
        console.error('❌ Falha ao dar JSON.parse:', e.message);
        process.exit(1);
    }
} else {
    console.error('❌ Regex não encontrou nada!');
    process.exit(1);
}

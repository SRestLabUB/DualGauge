const fs = require('fs');
const acorn = require('acorn');
const estraverse = require('estraverse');
const escodegen = require('escodegen');

const inputFile = process.argv[2];
const outputFile = process.argv[3];

if (!inputFile || !outputFile) {
    console.error('Usage: node js_instrumenter.js <input_file> <output_file>');
    process.exit(1);
}

try {
    const code = fs.readFileSync(inputFile, 'utf8');
    const ast = acorn.parse(code, { locations: true, ecmaVersion: 2020, sourceType: 'module' });

    function createLogStatement(line) {
        return {
            type: 'ExpressionStatement',
            expression: {
                type: 'CallExpression',
                callee: {
                    type: 'MemberExpression',
                    computed: false,
                    object: { type: 'Identifier', name: 'console' },
                    property: { type: 'Identifier', name: 'log' }
                },
                arguments: [
                    { type: 'Literal', value: `TRACE:${line}`, raw: `"TRACE:${line}"` }
                ]
            }
        };
    }

    const outputAst = estraverse.replace(ast, {
        enter: function (node) {
            if (node.type === 'BlockStatement' || node.type === 'Program') {
                const newBody = [];
                node.body.forEach(statement => {
                    if (statement.loc) {
                        newBody.push(createLogStatement(statement.loc.start.line));
                    }
                    newBody.push(statement);
                });
                node.body = newBody;
                return node;
            }
        }
    });

    const instrumentedCode = escodegen.generate(outputAst);
    fs.writeFileSync(outputFile, instrumentedCode);
    console.log(`Instrumentation successful: ${outputFile}`);

} catch (e) {
    console.error('Instrumentation failed:', e);
    process.exit(1);
}

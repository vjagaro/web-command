const Bundler = require('parcel-bundler');
const Path = require('path');

process.env.NODE_ENV = process.env.NODE_ENV || 'production';

(new Bundler([
    Path.join(__dirname, './client/*')
], {
    outDir: './web_command/static',
    contentHash: false,
    production: true,
    sourceMaps: false
})).bundle();

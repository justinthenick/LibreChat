const { isRuntimeToolModule } = require('./tools');

describe('isRuntimeToolModule', () => {
  it('accepts runtime JavaScript tool modules', () => {
    expect(isRuntimeToolModule('AzureAISearch.js')).toBe(true);
    expect(isRuntimeToolModule('StableDiffusion.js')).toBe(true);
    expect(isRuntimeToolModule('credentials.js')).toBe(true);
  });

  it('rejects Jest spec and test modules before require()', () => {
    expect(isRuntimeToolModule('AzureAISearch.spec.js')).toBe(false);
    expect(isRuntimeToolModule('StableDiffusion.spec.js')).toBe(false);
    expect(isRuntimeToolModule('OpenWeather.test.js')).toBe(false);
  });

  it('rejects non-JavaScript files', () => {
    expect(isRuntimeToolModule('README.md')).toBe(false);
    expect(isRuntimeToolModule('tool.json')).toBe(false);
  });
});

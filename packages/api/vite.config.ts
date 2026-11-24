/// <reference types="vitest" />
import { defineConfig } from "vite";
import path from "node:path";
import dts from "vite-plugin-dts";
import pkg from "./package.json";

export default defineConfig(({ command, mode }) => {
  const isPro = command === "build" && mode !== "hotBuild";

  const inputList = ["src/index.ts"];

  return {
    test: {
      globals: true,
      coverage: {
        provider: "istanbul", // or 'v8'
        reporter: ["text", "json", "html"],
        include: ["src/**/*.ts?(x)"],
      },
    },
    plugins: [
      dts({
        include: [
          "src/**/*.ts",
          "src/**/*.tsx",
          "src/**/*.d.ts",
          "src/**/*.json",
        ],
        exclude: ["**/__tests__/**"],
        outDir: "./types",
        rollupTypes: isPro,
      }),
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    json: {
      namedExports: false,
      stringify: false,
    },
    build: {
      minify: isPro,
      emptyOutDir: true,
      lib: {
        entry: inputList,
      },
      rollupOptions: {
        external: [
          ...Object.keys(pkg.dependencies || {}),
          ...Object.keys(pkg.peerDependencies || {}),
        ],
        input: inputList,
        output: [
          {
            format: "es",
            entryFileNames: "[name].mjs",
            dir: "./es",
            ...(isPro
              ? {}
              : {
                  preserveModules: true,
                  preserveModulesRoot: "src",
                }),
          },
          {
            format: "cjs",
            exports: "named",
            entryFileNames: "[name].cjs",
            dir: "./lib",
            ...(isPro
              ? {}
              : {
                  preserveModules: true,
                  preserveModulesRoot: "src",
                }),
          },
        ],
      },
    },
  };
});

/// <reference types="vitest" />
import { defineConfig } from "vite";
import fs from "node:fs";
import path from "node:path";
import dts from "vite-plugin-dts";
import pkg from "./package.json";

export default defineConfig(({ command, mode }) => {
  const isPro = command === "build" && mode !== "hotBuild";

  // 两个出口：结构（主入口）与参考资源（./reference）。
  const inputList = ["src/index.ts", "src/reference.ts"];

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
        // 本包是 "type": "module"，.d.ts 一律按 ES 模块解读；给 require 条件另备一份 .d.cts，
        // 否则 moduleResolution 为 node16 的 CommonJS 使用方会报 TS1479。声明文件自成一体，照抄即可。
        afterBuild: () => {
          for (const entry of ["index", "reference"]) {
            const declaration = path.resolve(__dirname, `types/${entry}.d.ts`);
            if (fs.existsSync(declaration)) {
              fs.copyFileSync(
                declaration,
                path.resolve(__dirname, `types/${entry}.d.cts`),
              );
            }
          }
        },
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

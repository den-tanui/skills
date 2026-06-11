#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");

// Configuration
const SKILLS_DIR = "/home/opt/my-skills";
const README_PATH = path.join(SKILLS_DIR, "README.md");
const INDEX_PATH = path.join(SKILLS_DIR, "SKILL_INDEX.md");

/**
 * Find all SKILL.md files recursively
 */
function findSkillFiles(dir = SKILLS_DIR) {
	let results = [];
	const items = fs.readdirSync(dir, { withFileTypes: true });

	for (const item of items) {
		const fullPath = path.join(dir, item.name);
		if (item.isDirectory()) {
			results = results.concat(findSkillFiles(fullPath));
		} else if (item.name === "SKILL.md") {
			results.push(fullPath);
		}
	}

	return results;
}

/**
 * Parse frontmatter from SKILL.md file
 */
function parseSkillFrontmatter(filePath) {
	try {
		const content = fs.readFileSync(filePath, "utf8");

		// Extract frontmatter (between --- lines)
		const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
		if (!frontmatterMatch) {
			console.warn(`No frontmatter found in ${filePath}`);
			return null;
		}

		const frontmatter = yaml.load(frontmatterMatch[1]);

		// Get relative path for display
		const relativePath = path.relative(SKILLS_DIR, filePath);
		const dirPath = path.dirname(relativePath);

		return {
			name: frontmatter.name || path.basename(path.dirname(filePath)),
			description: frontmatter.description || "No description provided",
			path: relativePath,
			dir: dirPath === "." ? "./" : dirPath + "/",
		};
	} catch (error) {
		console.error(`Error parsing ${filePath}:`, error.message);
		return null;
	}
}

/**
 * Generate markdown index
 */
function generateIndex(skills) {
	// Sort skills by name
	skills.sort((a, b) => a.name.localeCompare(b.name));

	const indexContent = `# My Skills Index

This is an automatically generated index of all skills in this repository.

## Skills List

${skills
	.map((skill) => {
		const displayPath =
			skill.dir === "./" ? skill.dir + skill.path : skill.path;
		return `### [${skill.name}](${displayPath})

${skill.description.trim()}`;
	})
	.join("\n\n")}

---

*Generated on ${new Date().toISOString().split("T")[0]}*\n
*Total skills: ${skills.length}*
`;

	return indexContent;
}

/**
 * Main function
 */
function main() {
	console.log("🔍 Discovering skills...");

	const skillFiles = findSkillFiles();
	console.log(`📁 Found ${skillFiles.length} SKILL.md files`);

	const skills = skillFiles
		.map((file) => parseSkillFrontmatter(file))
		.filter((skill) => skill !== null);

	console.log(`✅ Parsed ${skills.length} valid skills`);

	const indexContent = generateIndex(skills);

	// Write to both README.md and SKILL_INDEX.md
	fs.writeFileSync(README_PATH, indexContent, "utf8");
	fs.writeFileSync(INDEX_PATH, indexContent, "utf8");

	console.log(`📝 Updated ${README_PATH}`);
	console.log(`📝 Updated ${INDEX_PATH}`);
	console.log("✨ Index generation complete!");
}

// Run main function
if (require.main === module) {
	main();
}

module.exports = { findSkillFiles, parseSkillFrontmatter, generateIndex, main };

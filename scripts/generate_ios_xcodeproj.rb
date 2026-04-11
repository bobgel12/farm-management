#!/usr/bin/env ruby
require "xcodeproj"
require "fileutils"

ROOT = File.expand_path("..", __dir__)
IOS_DIR = File.join(ROOT, "ios")
APP_DIR = File.join(IOS_DIR, "FarmManagementApp")
CORE_DIR = File.join(IOS_DIR, "FarmManagementCore", "Sources", "FarmManagementCore")
PROJECT_PATH = File.join(IOS_DIR, "FarmManagementApp.xcodeproj")

FileUtils.rm_rf(PROJECT_PATH)

project = Xcodeproj::Project.new(PROJECT_PATH)
project.root_object.attributes["LastUpgradeCheck"] = "1600"

app_target = project.new_target(:application, "FarmManagementApp", :ios, "16.0")
core_target = project.new_target(:framework, "FarmManagementCore", :ios, "16.0")

app_target.build_configurations.each do |config|
  config.build_settings["PRODUCT_BUNDLE_IDENTIFIER"] = "com.farmmanagement.ios"
  config.build_settings["INFOPLIST_FILE"] = "FarmManagementApp/Config/Info.plist"
  config.build_settings["SWIFT_VERSION"] = "5.0"
  config.build_settings["IPHONEOS_DEPLOYMENT_TARGET"] = "16.0"
  config.build_settings["CODE_SIGN_STYLE"] = "Automatic"
  config.build_settings["TARGETED_DEVICE_FAMILY"] = "1"
  config.build_settings["LD_RUNPATH_SEARCH_PATHS"] = ["$(inherited)", "@executable_path/Frameworks"]
end

core_target.build_configurations.each do |config|
  config.build_settings["PRODUCT_BUNDLE_IDENTIFIER"] = "com.farmmanagement.core"
  config.build_settings["DEFINES_MODULE"] = "YES"
  config.build_settings["MACH_O_TYPE"] = "mh_dylib"
  config.build_settings["GENERATE_INFOPLIST_FILE"] = "YES"
  config.build_settings["SWIFT_VERSION"] = "5.0"
  config.build_settings["IPHONEOS_DEPLOYMENT_TARGET"] = "16.0"
  config.build_settings["CODE_SIGN_STYLE"] = "Automatic"
end

app_group = project.main_group.find_subpath("FarmManagementApp", true)
core_group = project.main_group.find_subpath("FarmManagementCore", true)

Dir.glob(File.join(APP_DIR, "**/*.swift")).sort.each do |file|
  relative = file.sub("#{IOS_DIR}/", "")
  ref = app_group.find_file_by_path(relative) || app_group.new_file(relative)
  app_target.source_build_phase.add_file_reference(ref, true)
end

plist_path = "FarmManagementApp/Config/Info.plist"
app_group.find_file_by_path(plist_path) || app_group.new_file(plist_path)

Dir.glob(File.join(CORE_DIR, "**/*.swift")).sort.each do |file|
  relative = file.sub("#{IOS_DIR}/", "")
  ref = core_group.find_file_by_path(relative) || core_group.new_file(relative)
  core_target.source_build_phase.add_file_reference(ref, true)
end

app_target.add_dependency(core_target)
framework_ref = core_target.product_reference
app_target.frameworks_build_phase.add_file_reference(framework_ref)
embed_phase = app_target.new_copy_files_build_phase("Embed Frameworks")
embed_phase.symbol_dst_subfolder_spec = :frameworks
embed_phase.add_file_reference(framework_ref)

project.save
puts "Generated #{PROJECT_PATH}"

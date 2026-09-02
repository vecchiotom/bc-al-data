using System;using System.Linq;using System.Reflection;using System.Resources;
var dir=Environment.GetEnvironmentVariable("STORE")!;
var asm=Assembly.LoadFrom(System.IO.Path.Combine(dir,"Microsoft.Dynamics.Nav.CodeAnalysis.dll"));
Console.WriteLine("=== manifest resources ===");
foreach(var r in asm.GetManifestResourceNames())Console.WriteLine(r);
Console.WriteLine("=== types w/ Message/Resource/Provider ===");
foreach(var t in asm.GetTypes().Where(t=>t.Name.Contains("Message")||t.Name.Contains("Resource")||t.Name.Contains("MessageProvider")))
 Console.WriteLine($"{t.FullName}  ({string.Join(",",t.GetMethods(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static|BindingFlags.Instance).Where(m=>m.DeclaringType==t).Select(m=>m.Name).Distinct().Take(20))})");

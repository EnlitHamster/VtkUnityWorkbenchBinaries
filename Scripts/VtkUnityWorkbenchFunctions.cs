using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Text;
using System;

using ThreeDeeHeartPlugins;
using VtkUnityWorkbench;

namespace VtkUnityWorkbench
{
    public static class VtkUnityWorkbenchPlugin
    {
        private static Dictionary<string, IComponentFactory> sComponentFactories;

        ///////////////////////////////////////////////////
        // Getter for primitive attributes
        public static T GetProperty<T>(
            int shapeId,
            string propertyName,
            string expectedReturn)
            where T : IConvertible
        {
            StringBuilder buffer = new StringBuilder();
            VtkToUnityPlugin.GetShapePrimitiveProperty(shapeId, propertyName, expectedReturn, buffer);

            if (buffer.ToString().StartsWith("err"))
            {
                string msg = buffer.ToString().Replace("err::(", "").Replace(")", "");
                throw new VtkUnityFetchException(msg);
            }
            else
            {
                string val = buffer.ToString().Replace("val::(", "").Replace(")", "");
                return VtkUnityWorkbenchHelpers.StringTo<T>(val);
            }
        }

        ///////////////////////////////////////////////////
        // Setter for primitive attributes
        public static void SetProperty<T>(
            int shapeId,
            string propertyName,
            T newValue)
            where T : IConvertible
        {
            try
            {
                string strNewValue = (string)Convert.ChangeType(newValue, typeof(string));
                VtkToUnityPlugin.SetShapePrimitiveProperty(shapeId, propertyName, strNewValue);
            }
            catch (Exception)
            {
                throw new VtkUnityConversionException("string", typeof(T).ToString());
            }
        }

        public static Dictionary<string, Type> GetDescriptor(
            int shapeId)
        {
            //StringBuilder buffer = new StringBuilder();
            //VtkToUnityPlugin.GetDescriptor(shapeId, buffer);
            //if (buffer.ToString().StartsWith("err"))
            //{
            //    string msg = buffer.ToString().Replace("err::(", "").Replace(")", "");
            //    throw new VtkUnityFetchException(msg);
            //}
            //else
            //{
            //    Dictionary<string, Type> descriptor = new Dictionary<string, Type>();
            //    string strDesc = buffer.ToString();
            //    string[] attribs = strDesc.Split(',');
            //    foreach (string attrib in attribs)
            //    {
            //        string[] pair = attrib.Split(':');
            //        descriptor.Add(pair[0], Type.GetType(pair[1]));
            //    }
            //    return descriptor;
            //}
            Dictionary<string, Type> descriptor = new Dictionary<string, Type>();
            descriptor.Add("Height", Type.GetType("System.Double"));
            descriptor.Add("Radius", Type.GetType("System.Double"));
            descriptor.Add("Resolution", Type.GetType("System.Int32"));
            descriptor.Add("Capping", Type.GetType("System.Int32"));
            descriptor.Add("Center", Type.GetType("VtkUnityWorkbench.Double3"));
            descriptor.Add("Direction", Type.GetType("VtkUnityWorkbench.Double3"));
            return descriptor;
        }

        ///////////////////////////////////////////////////
        // Registration to the plugin for UI call
        public static void RegisterComponentFactory(
            string callbackComponent, 
            IComponentFactory factory)
        {
            if (sComponentFactories == null)
            {
                sComponentFactories = new Dictionary<string, IComponentFactory>();
            }

            sComponentFactories.Add(callbackComponent, factory);
        }

        ///////////////////////////////////////////////////
        // Shows the UI for the registered component
        public static void ShowComponentFor(
            string callbackComponent)
        {
            if (sComponentFactories != null)
            {
                if (sComponentFactories.ContainsKey(callbackComponent))
                {
                    sComponentFactories[callbackComponent].Show();
                }
                else
                {
                    throw new VtkUnityComponentNotFoundException(callbackComponent);
                }
            }
        }

        ///////////////////////////////////////////////////
        // Destroys the UI for the registered component
        public static void DestroyComponentFor(
            string callbackComponent)
        {
            if (sComponentFactories != null)
            {
                if (sComponentFactories.ContainsKey(callbackComponent))
                {
                    sComponentFactories[callbackComponent].Destroy();
                }
                else
                {
                    throw new VtkUnityComponentNotFoundException(callbackComponent);
                }
            }
        }
    }
}
